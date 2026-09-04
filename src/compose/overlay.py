"""在合成图上叠加标注。"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def draw_typhoon_marker(
    image_path: Path,
    xy: tuple[int, int],
    *,
    label: str = "TY",
) -> bool:
    """在已保存的 RGB 图上画台风中心标记（圆 + 十字 + 短字）并写回。

    Args:
        image_path: 壁纸文件路径。
        xy: 像素坐标 ``(x, y)``。
        label: 中心旁短标签。

    Returns:
        成功写回为 True；失败为 False。
    """
    try:
        with Image.open(image_path) as img:
            canvas = img.convert("RGB")
            draw = ImageDraw.Draw(canvas)
            x, y = xy
            side = min(canvas.size)
            radius = max(6, side // 180)
            arm = max(10, side // 90)
            color = (241, 166, 39)
            outline = (20, 20, 20)
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
            draw.line((x - arm, y, x + arm, y), fill=color, width=max(2, radius // 4))
            draw.line((x, y - arm, x, y + arm), fill=color, width=max(2, radius // 4))
            draw.line((x - arm, y, x + arm, y), fill=outline, width=1)
            draw.line((x, y - arm, x, y + arm), fill=outline, width=1)
            font = ImageFont.load_default()
            text_xy = (x + radius + 4, y - radius - 2)
            draw.text((text_xy[0] + 1, text_xy[1] + 1), label, fill=outline, font=font)
            draw.text(text_xy, label, fill=color, font=font)
            canvas.save(image_path)
        logging.info("Typhoon marker drawn at %s on %s", xy, image_path)
        return True
    except OSError:
        logging.exception("Failed to draw typhoon marker on %s", image_path)
        return False
