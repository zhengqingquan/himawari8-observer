"""等分瓦片合成与可选黑边修边。"""

from __future__ import annotations

import ctypes
import logging
import math
import os
from pathlib import Path
from time import struct_time
from typing import Any, NamedTuple

from PIL import Image, ImageChops, ImageFilter

from src.compose.geo import latlon_to_himawari_fd_xy
from src.compose.solar import points_on_solar_mu_circle
from src.metadata.app_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)


class DebandParams(NamedTuple):
    """去色带算法参数（默认等同历史硬编码）。"""

    blur_radius: float = 10.0
    diff_scale: int = 5
    noise_sigma: float = 2.0
    black_luma_max: int = 2
    terminator_mu_half: float = 0.20
    terminator_mu_steps: int = 15
    terminator_samples: int = 720
    terminator_mask_side: int = 512
    terminator_mask_blur: float = 6.0
    terminator_stamp_r: int = 2

    def as_settings_dict(self) -> dict[str, float | int]:
        """落盘 / settings 用的普通 dict。"""
        return {name: getattr(self, name) for name in self._fields}

    def as_fingerprint_list(self) -> list[float | int]:
        """成图指纹第 11 项：固定顺序的 10 个数。"""
        return [getattr(self, name) for name in self._fields]

    @classmethod
    def from_fingerprint_list(cls, value: Any) -> DebandParams | None:
        """接受完整 10 项数值序列；非法则 ``None``。"""
        if isinstance(value, cls):
            return value
        if not isinstance(value, (list, tuple)) or len(value) != len(cls._fields):
            return None
        try:
            return cls(
                float(value[0]),
                int(value[1]),
                float(value[2]),
                int(value[3]),
                float(value[4]),
                int(value[5]),
                int(value[6]),
                int(value[7]),
                float(value[8]),
                int(value[9]),
            )
        except (TypeError, ValueError):
            return None


DEFAULT_DEBAND = DebandParams()

_SM_CXSCREEN = 0
_SM_CYSCREEN = 1


def get_primary_screen_size() -> tuple[int, int]:
    """用 Win32 ``GetSystemMetrics`` 读取主屏像素尺寸（不截屏）。

    Returns:
        ``(width, height)``。

    Raises:
        OSError: API 返回非正尺寸时。
    """
    width = int(ctypes.windll.user32.GetSystemMetrics(_SM_CXSCREEN))
    height = int(ctypes.windll.user32.GetSystemMetrics(_SM_CYSCREEN))
    if width <= 0 or height <= 0:
        raise OSError(f"GetSystemMetrics returned invalid screen size: {width}x{height}")
    return width, height


def compute_margin_layout(
    image_side: int,
    screen_width: int,
    screen_height: int,
    *,
    top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
) -> tuple[int, int, int, int]:
    """计算修边画布尺寸与正方形内容区左上角偏移。

    Returns:
        ``(canvas_width, canvas_height, image_x, image_y)``。
    """
    top_expand = int(image_side * top_percent / 100.0)
    bottom_expand = int(image_side * bottom_percent / 100.0)
    content_height = image_side + top_expand + bottom_expand
    scale = content_height / screen_height
    canvas_width = int(math.ceil(screen_width * scale))
    canvas_height = content_height
    image_x = int(math.ceil((canvas_width - image_side) / 2))
    image_y = top_expand
    return canvas_width, canvas_height, image_x, image_y


def _paste_tiles(joint: Image.Image, pic, *, origin_x: int = 0, origin_y: int = 0) -> None:
    axis_x = 0
    axis_y = 0
    for slot in pic.tiles.values():
        with Image.open(slot.path) as tile:
            joint.paste(
                tile,
                (origin_x + pic.pic_pixel * axis_x, origin_y + pic.pic_pixel * axis_y),
            )
        axis_x += 1
        if axis_x >= pic.grid_size:
            axis_x = 0
            axis_y += 1


def _resolve_disk_origin(
    image_size: tuple[int, int],
    disk_side: int,
    *,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    screen_size: tuple[int, int] | None,
) -> tuple[int, int]:
    """推断正方形圆盘在画布上的左上角；正方形原图为 ``(0, 0)``。"""
    width, height = image_size
    if width == disk_side and height == disk_side:
        return (0, 0)
    if auto_adjust:
        if screen_size is None:
            screen_width, screen_height = get_primary_screen_size()
        else:
            screen_width, screen_height = screen_size
        _, _, image_x, image_y = compute_margin_layout(
            disk_side,
            screen_width,
            screen_height,
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
        )
        return (image_x, image_y)
    return (max(0, (width - disk_side) // 2), max(0, (height - disk_side) // 2))


def build_terminator_belt_mask(
    side: int,
    observation_time: struct_time,
    *,
    params: DebandParams | None = None,
) -> Image.Image:
    """构建晨昏带软掩码（L）：晨昏线附近高、远离处为 0。

    在低分辨率上按太阳点积 ``μ`` 采样圆环并取最大权重，再模糊、峰值归一、放大到 ``side``。
    """
    if side <= 0:
        raise ValueError(f"disk side must be positive, got {side}")
    cfg = params if params is not None else DEFAULT_DEBAND
    render = min(side, cfg.terminator_mask_side)
    buf = bytearray(render * render)
    half = cfg.terminator_mu_half
    steps = cfg.terminator_mu_steps
    stamp_r = cfg.terminator_stamp_r
    for step in range(steps):
        t = step / (steps - 1) if steps > 1 else 0.5
        mu = -half + 2.0 * half * t
        weight = int(round(255.0 * max(0.0, 1.0 - abs(mu) / half)))
        if weight <= 0:
            continue
        for lat, lon in points_on_solar_mu_circle(
            observation_time,
            mu,
            sample_count=cfg.terminator_samples,
        ):
            xy = latlon_to_himawari_fd_xy(lat, lon, render)
            if xy is None:
                continue
            cx, cy = xy
            for dy in range(-stamp_r, stamp_r + 1):
                py = cy + dy
                if py < 0 or py >= render:
                    continue
                for dx in range(-stamp_r, stamp_r + 1):
                    px = cx + dx
                    if px < 0 or px >= render:
                        continue
                    index = py * render + px
                    if weight > buf[index]:
                        buf[index] = weight
    mask = Image.frombytes("L", (render, render), bytes(buf))
    blurred = mask.filter(ImageFilter.GaussianBlur(cfg.terminator_mask_blur))
    mask.close()
    peak = blurred.getextrema()[1]
    if peak > 0 and peak < 255:
        scale = 255.0 / peak
        normalized = blurred.point(lambda p: min(255, int(p * scale)))
        blurred.close()
        blurred = normalized
    if render == side:
        return blurred
    scaled = blurred.resize((side, side), Image.Resampling.BILINEAR)
    blurred.close()
    return scaled


def reduce_color_banding(
    image: Image.Image,
    *,
    observation_time: struct_time | None = None,
    disk_side: int | None = None,
    disk_origin: tuple[int, int] = (0, 0),
    params: DebandParams | None = None,
) -> Image.Image:
    """减轻 8 bit 平滑渐变中的色带（posterization）。

    用高斯邻域均值与原图像素差做软掩码：差小的平坦量化区靠向均值以打散台阶；
    差大的纹理/边缘保留细节。再加微粒噪点；近黑像素（太空、修边黑边）保持原样。

    传入 ``observation_time`` 与 ``disk_side`` 时，仅在晨昏带合成去色带结果，
    昼心与夜心保留原像素（产品默认路径）。

    Args:
        image: RGB 图（其它模式会先转成 RGB）。
        observation_time: UTC 观测时间；与 ``disk_side`` 同时提供时启用晨昏带限制。
        disk_side: 正方形全盘边长（像素）。
        disk_origin: 全盘在 ``image`` 上的左上角（修边画布用）。
        params: 去色带参数；缺省用 ``DEFAULT_DEBAND``。

    Returns:
        处理后的新 RGB 图（调用方负责关闭）。
    """
    cfg = params if params is not None else DEFAULT_DEBAND
    rgb = image.convert("RGB") if image.mode != "RGB" else image
    avg = rgb.filter(ImageFilter.GaussianBlur(cfg.blur_radius))
    diff = ImageChops.difference(rgb, avg).convert("L")
    diff_scale = cfg.diff_scale
    mask = diff.point(lambda p: max(0, min(255, 255 - p * diff_scale)))
    smoothed = Image.composite(avg, rgb, mask)
    noise = Image.effect_noise(rgb.size, cfg.noise_sigma).convert("RGB")
    grained = ImageChops.add(smoothed, noise, scale=1.0, offset=-128)
    spatial = None
    limited = grained
    if observation_time is not None and disk_side is not None:
        disk_mask = build_terminator_belt_mask(disk_side, observation_time, params=cfg)
        if rgb.size == (disk_side, disk_side) and disk_origin == (0, 0):
            spatial = disk_mask
        else:
            spatial = Image.new("L", rgb.size, 0)
            spatial.paste(disk_mask, disk_origin)
            disk_mask.close()
        limited = Image.composite(grained, rgb, spatial)
    black_max = cfg.black_luma_max
    keep_black = rgb.convert("L").point(lambda p: 0 if p <= black_max else 255)
    result = Image.composite(limited, rgb, keep_black)
    avg.close()
    diff.close()
    mask.close()
    smoothed.close()
    noise.close()
    grained.close()
    if spatial is not None:
        spatial.close()
    if limited is not grained:
        limited.close()
    keep_black.close()
    if rgb is not image:
        rgb.close()
    return result


def apply_deband_to_file(
    src: Path | str,
    dest: Path | str,
    *,
    observation_time: struct_time,
    disk_side: int,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    screen_size: tuple[int, int] | None = None,
    params: DebandParams | None = None,
) -> None:
    """读取 ``src``，仅对晨昏带减轻色带后写入 ``dest``（可与 ``src`` 相同）。"""
    with Image.open(src) as image:
        origin = _resolve_disk_origin(
            image.size,
            disk_side,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            screen_size=screen_size,
        )
        processed = reduce_color_banding(
            image,
            observation_time=observation_time,
            disk_side=disk_side,
            disk_origin=origin,
            params=params,
        )
        try:
            processed.save(dest)
        finally:
            processed.close()


def _save_rgb(image: Image.Image, path: Path | str, *, deband: bool = False) -> None:
    """保存 RGB 壁纸图；``deband=True`` 时先做去色带再落盘。

    无观测时间上下文时整图处理（合成路径遗留）；产品路径请用 ``apply_deband_to_file``。
    """
    if not deband:
        image.save(path)
        return
    processed = reduce_color_banding(image)
    try:
        processed.save(path)
    finally:
        processed.close()


def compose_equal_image(pic, *, deband: bool = False) -> None:
    """将多张瓦片合成为一张等分完整图，并保存到 ``pic.final_path_equal``。

    Args:
        pic: 等分瓦片图实例（需已下载完成）。
        deband: 是否在保存前减轻色带；默认关闭。
    """
    joint = None
    try:
        joint = Image.new("RGB", (pic.pic_side, pic.pic_side))
        _paste_tiles(joint, pic)
        _save_rgb(joint, pic.final_path_equal, deband=deband)
    except Exception:
        logging.exception("Failed to compose equal image for grade %s", pic.grade)
        raise
    finally:
        if joint is not None:
            joint.close()
    logging.info(
        "Composed equal image saved: %s",
        os.path.abspath(pic.final_path_equal),
    )


def compose_equal_image_with_margins(
    pic,
    output_path: Path | str,
    *,
    top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    screen_size: tuple[int, int] | None = None,
    deband: bool = False,
) -> Path:
    """将瓦片直接贴到修边画布并保存，避免先合成正方形再编解码。

    Args:
        pic: 等分瓦片图实例（需已下载完成）。
        output_path: 修边后壁纸输出路径。
        top_percent: 顶边黑边占原图边长的百分比。
        bottom_percent: 底边黑边占原图边长的百分比。
        screen_size: 可选 ``(width, height)``；默认主屏 ``GetSystemMetrics`` 尺寸。
        deband: 是否在保存前减轻色带；默认关闭。

    Returns:
        输出路径（``Path``）。
    """
    out = Path(output_path)
    if screen_size is None:
        screen_width, screen_height = get_primary_screen_size()
    else:
        screen_width, screen_height = screen_size

    canvas_width, canvas_height, image_x, image_y = compute_margin_layout(
        pic.pic_side,
        screen_width,
        screen_height,
        top_percent=top_percent,
        bottom_percent=bottom_percent,
    )
    logging.info(
        "Margin layout: screen=%sx%s source=%spx margins=%s/%s canvas=%sx%s paste=(%s,%s)",
        screen_width,
        screen_height,
        pic.pic_side,
        top_percent,
        bottom_percent,
        canvas_width,
        canvas_height,
        image_x,
        image_y,
    )

    joint = None
    try:
        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        _paste_tiles(joint, pic, origin_x=image_x, origin_y=image_y)
        out.parent.mkdir(parents=True, exist_ok=True)
        _save_rgb(joint, out, deband=deband)
    except Exception:
        logging.exception(
            "Failed to compose equal image with margins for grade %s -> %s",
            pic.grade,
            out,
        )
        raise
    finally:
        if joint is not None:
            joint.close()
    logging.info("Margin-adjusted wallpaper saved: %s", os.path.abspath(out))
    return out


def apply_margins(
    src: Path | str,
    image_side: int,
    dest: Path | str,
    *,
    top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    screen_size: tuple[int, int] | None = None,
    deband: bool = False,
) -> None:
    """将正方形等分合成图嵌入与屏幕同比例的黑边画布。

    Args:
        src: 原文件路径。
        image_side: 原图边长（像素）。
        dest: 输出保存路径。
        top_percent: 顶边黑边占原图边长的百分比。
        bottom_percent: 底边黑边占原图边长的百分比。
        screen_size: 可选 ``(width, height)``；默认主屏尺寸。
        deband: 是否在保存前减轻色带；默认关闭。
    """
    joint = None
    try:
        if screen_size is None:
            screen_width, screen_height = get_primary_screen_size()
        else:
            screen_width, screen_height = screen_size

        canvas_width, canvas_height, image_x, image_y = compute_margin_layout(
            image_side,
            screen_width,
            screen_height,
            top_percent=top_percent,
            bottom_percent=bottom_percent,
        )
        logging.info(
            "Margin layout: screen=%sx%s source=%spx margins=%s/%s canvas=%sx%s paste=(%s,%s)",
            screen_width,
            screen_height,
            image_side,
            top_percent,
            bottom_percent,
            canvas_width,
            canvas_height,
            image_x,
            image_y,
        )

        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        with Image.open(src) as img:
            joint.paste(img, (image_x, image_y))
        _save_rgb(joint, dest, deband=deband)
    except Exception:
        logging.exception("Failed to apply margins: src=%s out=%s", src, dest)
        raise
    finally:
        if joint is not None:
            joint.close()
    logging.info("Margin-adjusted wallpaper saved: %s", dest)
