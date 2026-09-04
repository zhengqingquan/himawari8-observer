"""在合成图上叠加标注。"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_MarkerStyle = str  # "crosshair" | "corners"


def _stroke_line(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    color: tuple[int, int, int],
    outline: tuple[int, int, int],
    width: int,
) -> None:
    draw.line(xy, fill=outline, width=width + 1)
    draw.line(xy, fill=color, width=width)


def _draw_center_cross(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    *,
    arm: int,
    color: tuple[int, int, int],
    outline: tuple[int, int, int],
    width: int,
) -> None:
    _stroke_line(draw, (x - arm, y, x + arm, y), color=color, outline=outline, width=width)
    _stroke_line(draw, (x, y - arm, x, y + arm), color=color, outline=outline, width=width)


def _draw_crosshair(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    *,
    side: int,
    color: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> int:
    """圆 + 十字；返回半宽供标签定位。"""
    radius = max(6, side // 180)
    arm = max(10, side // 90)
    line_w = max(2, radius // 4)
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        outline=outline,
        width=max(2, radius // 3),
    )
    draw.ellipse(
        (x - radius + 2, y - radius + 2, x + radius - 2, y + radius - 2),
        outline=color,
        width=max(2, radius // 3),
    )
    _draw_center_cross(
        draw, x, y, arm=arm, color=color, outline=outline, width=line_w
    )
    return radius


def _draw_corner_brackets(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    *,
    side: int,
    color: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> int:
    """四角折线 + 中心十字；返回半宽供标签定位。"""
    half = max(8, side // 120)
    corner = max(4, half // 2)
    line_w = max(2, half // 4)
    arm = max(5, half // 2)
    # ⌜ ⌝ ⌞ ⌟
    corners = (
        ((x - half, y - half, x - half + corner, y - half), (x - half, y - half, x - half, y - half + corner)),
        ((x + half - corner, y - half, x + half, y - half), (x + half, y - half, x + half, y - half + corner)),
        ((x - half, y + half - corner, x - half, y + half), (x - half, y + half, x - half + corner, y + half)),
        ((x + half, y + half - corner, x + half, y + half), (x + half - corner, y + half, x + half, y + half)),
    )
    for horiz, vert in corners:
        _stroke_line(draw, horiz, color=color, outline=outline, width=line_w)
        _stroke_line(draw, vert, color=color, outline=outline, width=line_w)
    _draw_center_cross(
        draw, x, y, arm=arm, color=color, outline=outline, width=line_w
    )
    return half


def draw_typhoon_marker(
    image_path: Path,
    xy: tuple[int, int],
    *,
    label: str = "TY",
    color: tuple[int, int, int] = (241, 166, 39),
    style: _MarkerStyle = "corners",
) -> bool:
    """在已保存的 RGB 图上画标记并写回。

    Args:
        image_path: 壁纸文件路径。
        xy: 像素坐标 ``(x, y)``。
        label: 中心旁短标签。
        color: 标记主色（RGB）；默认台风橙黄。
        style: ``"corners"`` 四角折线 + 十字；``"crosshair"`` 圆 + 十字。

    Returns:
        成功写回为 True；失败为 False。
    """
    try:
        with Image.open(image_path) as img:
            canvas = img.convert("RGB")
            draw = ImageDraw.Draw(canvas)
            x, y = xy
            side = min(canvas.size)
            outline = (20, 20, 20)
            if style == "crosshair":
                half = _draw_crosshair(draw, x, y, side=side, color=color, outline=outline)
            else:
                half = _draw_corner_brackets(
                    draw, x, y, side=side, color=color, outline=outline
                )
            font = ImageFont.load_default()
            text_xy = (x + half + 4, y - half - 2)
            draw.text((text_xy[0] + 1, text_xy[1] + 1), label, fill=outline, font=font)
            draw.text(text_xy, label, fill=color, font=font)
            canvas.save(image_path)
        logging.info("Marker %s drawn at %s on %s", label, xy, image_path)
        return True
    except OSError:
        logging.exception("Failed to draw marker on %s", image_path)
        return False
