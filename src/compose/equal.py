"""等分瓦片合成与可选黑边修边。"""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path

from PIL import Image, ImageGrab

from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)


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


def compose_equal_image(pic) -> None:
    """将多张瓦片合成为一张等分完整图，并保存到 ``pic.final_path_equal``。

    Args:
        pic: 等分瓦片图实例（需已下载完成）。
    """
    joint = None
    try:
        joint = Image.new("RGB", (pic.pic_side, pic.pic_side))
        _paste_tiles(joint, pic)
        joint.save(pic.final_path_equal)
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
) -> Path:
    """将瓦片直接贴到修边画布并保存，避免先合成正方形再编解码。

    Args:
        pic: 等分瓦片图实例（需已下载完成）。
        output_path: 修边后壁纸输出路径。
        top_percent: 顶边黑边占原图边长的百分比。
        bottom_percent: 底边黑边占原图边长的百分比。
        screen_size: 可选 ``(width, height)``；默认 ``ImageGrab.grab().size``。

    Returns:
        输出路径（``Path``）。
    """
    out = Path(output_path)
    if screen_size is None:
        screen_width, screen_height = ImageGrab.grab().size
    else:
        screen_width, screen_height = screen_size

    canvas_width, canvas_height, image_x, image_y = compute_margin_layout(
        pic.pic_side,
        screen_width,
        screen_height,
        top_percent=top_percent,
        bottom_percent=bottom_percent,
    )
    logging.info("Screen resolution: %sx%s", screen_width, screen_height)
    logging.info("Source image side: %s px", pic.pic_side)
    logging.info(
        "Margin percents: top=%s bottom=%s",
        top_percent,
        bottom_percent,
    )
    logging.info("Wallpaper canvas size: %sx%s", canvas_width, canvas_height)
    logging.info("Paste origin for tiles: (%s, %s)", image_x, image_y)

    joint = None
    try:
        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        _paste_tiles(joint, pic, origin_x=image_x, origin_y=image_y)
        out.parent.mkdir(parents=True, exist_ok=True)
        joint.save(out)
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
) -> None:
    """将正方形等分合成图嵌入与屏幕同比例的黑边画布。

    Args:
        file: 原文件路径。
        margin: 原图边长（像素）。
        path: 输出保存路径。
        top_percent: 顶边黑边占原图边长的百分比。
        bottom_percent: 底边黑边占原图边长的百分比。
        screen_size: 可选 ``(width, height)``；默认截屏尺寸。
    """
    joint = None
    try:
        if screen_size is None:
            screen_width, screen_height = ImageGrab.grab().size
        else:
            screen_width, screen_height = screen_size
        logging.info("Screen resolution: %sx%s", screen_width, screen_height)
        logging.info("Source image side: %s px", margin)
        logging.info(
            "Margin percents: top=%s bottom=%s",
            top_percent,
            bottom_percent,
        )

        canvas_width, canvas_height, image_x, image_y = compute_margin_layout(
            margin,
            screen_width,
            screen_height,
            top_percent=top_percent,
            bottom_percent=bottom_percent,
        )
        logging.info("Wallpaper canvas size: %sx%s", canvas_width, canvas_height)
        logging.info("Paste offset for source image: (%s, %s)", image_x, image_y)

        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        with Image.open(file) as img:
            joint.paste(img, (image_x, image_y))
        joint.save(path)
    except Exception:
        logging.exception("Failed to apply margins: src=%s out=%s", file, path)
        raise
    finally:
        if joint is not None:
            joint.close()
    logging.info("Margin-adjusted wallpaper saved: %s", path)
