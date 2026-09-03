"""等分瓦片合成与可选黑边修边。"""

from __future__ import annotations

import logging
import math
import os

from PIL import Image, ImageGrab

from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)


def compose_equal_image(pic) -> None:
    """将多张瓦片合成为一张等分完整图，并保存到 ``pic.final_path_equal``。

    Args:
        pic: 等分瓦片图实例（需已下载完成）。
    """
    try:
        axis_x = 0
        axis_y = 0
        joint = Image.new("RGB", (pic.pic_side, pic.pic_side))
        for key, val in pic.tiles.items():
            img = Image.open(val[0])
            joint.paste(img, (pic.pic_pixel * axis_x, pic.pic_pixel * axis_y))
            axis_x += 1
            if axis_x >= pic.grid_size:
                axis_x = 0
                axis_y += 1
        joint.save(pic.final_path_equal)
    except Exception:
        logging.exception("Failed to compose equal image for grade %s", pic.grade)
        raise
    logging.info(
        "Composed equal image saved: %s",
        os.path.abspath(pic.final_path_equal),
    )


def apply_margins(
    file,
    margin,
    path,
    *,
    top_percent=DEFAULT_MARGIN_TOP_PERCENT,
    bottom_percent=DEFAULT_MARGIN_BOTTOM_PERCENT,
) -> None:
    """将正方形等分合成图嵌入与屏幕同比例的黑边画布。

    Args:
        file: 原文件路径。
        margin: 原图边长（像素）。
        path: 输出保存路径。
        top_percent: 顶边黑边占原图边长的百分比。
        bottom_percent: 底边黑边占原图边长的百分比。
    """
    try:
        screen_width, screen_height = ImageGrab.grab().size
        logging.info("Screen resolution: %sx%s", screen_width, screen_height)
        logging.info("Source image side: %s px", margin)
        logging.info(
            "Margin percents: top=%s bottom=%s",
            top_percent,
            bottom_percent,
        )

        top_expand = int(margin * top_percent / 100.0)
        bottom_expand = int(margin * bottom_percent / 100.0)
        content_height = margin + top_expand + bottom_expand

        scale = content_height / screen_height
        canvas_width = int(math.ceil(screen_width * scale))
        canvas_height = content_height
        logging.info("Wallpaper canvas size: %sx%s", canvas_width, canvas_height)

        image_x = int(math.ceil((canvas_width - margin) / 2))
        image_y = top_expand
        logging.info("Paste offset for source image: (%s, %s)", image_x, image_y)

        joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
        with Image.open(file) as img:
            joint.paste(img, (image_x, image_y))
        joint.save(path)
    except Exception:
        logging.exception("Failed to apply margins: src=%s out=%s", file, path)
        raise
    logging.info("Margin-adjusted wallpaper saved: %s", path)
