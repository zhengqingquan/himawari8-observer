"""等分瓦片合成与可选黑边修边。"""

from __future__ import annotations

import ctypes
import logging
import math
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from src.metadata.app_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)

# 去色带：邻域均值替换平坦量化区 + 微粒噪点；近黑（太空/黑边）保持原样。
_DEBAND_BLUR_RADIUS = 10.0
_DEBAND_DIFF_SCALE = 10
_DEBAND_NOISE_SIGMA = 3.5
_DEBAND_BLACK_LUMA_MAX = 2

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
    for _key, val in pic.tiles.items():
        with Image.open(val[0]) as tile:
            joint.paste(
                tile,
                (origin_x + pic.pic_pixel * axis_x, origin_y + pic.pic_pixel * axis_y),
            )
        axis_x += 1
        if axis_x >= pic.grid_size:
            axis_x = 0
            axis_y += 1


def reduce_color_banding(image: Image.Image) -> Image.Image:
    """减轻 8 bit 平滑渐变中的色带（posterization）。

    用高斯邻域均值与原图像素差做软掩码：差小的平坦量化区靠向均值以打散台阶；
    差大的纹理/边缘保留细节。再加微粒噪点；近黑像素（太空、修边黑边）保持原样。

    Args:
        image: RGB 图（其它模式会先转成 RGB）。

    Returns:
        处理后的新 RGB 图（调用方负责关闭）。
    """
    rgb = image.convert("RGB") if image.mode != "RGB" else image
    avg = rgb.filter(ImageFilter.GaussianBlur(_DEBAND_BLUR_RADIUS))
    diff = ImageChops.difference(rgb, avg).convert("L")
    mask = diff.point(lambda p: max(0, min(255, 255 - p * _DEBAND_DIFF_SCALE)))
    smoothed = Image.composite(avg, rgb, mask)
    noise = Image.effect_noise(rgb.size, _DEBAND_NOISE_SIGMA).convert("RGB")
    grained = ImageChops.add(smoothed, noise, scale=1.0, offset=-128)
    keep_black = rgb.convert("L").point(lambda p: 0 if p <= _DEBAND_BLACK_LUMA_MAX else 255)
    result = Image.composite(grained, rgb, keep_black)
    avg.close()
    diff.close()
    mask.close()
    smoothed.close()
    noise.close()
    grained.close()
    keep_black.close()
    if rgb is not image:
        rgb.close()
    return result


def apply_deband_to_file(src: Path | str, dest: Path | str) -> None:
    """读取 ``src``，减轻色带后写入 ``dest``（可与 ``src`` 相同）。"""
    with Image.open(src) as image:
        processed = reduce_color_banding(image)
        try:
            processed.save(dest)
        finally:
            processed.close()


def _save_rgb(image: Image.Image, path: Path | str, *, deband: bool = False) -> None:
    """保存 RGB 壁纸图；``deband=True`` 时先做去色带再落盘。"""
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
    file,
    margin,
    path,
    *,
    top_percent=DEFAULT_MARGIN_TOP_PERCENT,
    bottom_percent=DEFAULT_MARGIN_BOTTOM_PERCENT,
    screen_size: tuple[int, int] | None = None,
    deband: bool = False,
) -> None:
    """将正方形等分合成图嵌入与屏幕同比例的黑边画布。

    Args:
        file: 原文件路径。
        margin: 原图边长（像素）。
        path: 输出保存路径。
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
            margin,
            screen_width,
            screen_height,
            top_percent=top_percent,
            bottom_percent=bottom_percent,
        )
        logging.info(
            "Margin layout: screen=%sx%s source=%spx margins=%s/%s canvas=%sx%s paste=(%s,%s)",
            screen_width,
            screen_height,
            margin,
            top_percent,
            bottom_percent,
            canvas_width,
            canvas_height,
            image_x,
            image_y,
        )

        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        with Image.open(file) as img:
            joint.paste(img, (image_x, image_y))
        _save_rgb(joint, path, deband=deband)
    except Exception:
        logging.exception("Failed to apply margins: src=%s out=%s", file, path)
        raise
    finally:
        if joint is not None:
            joint.close()
    logging.info("Margin-adjusted wallpaper saved: %s", path)
