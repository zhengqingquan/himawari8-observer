"""
main.py

一次性入口：从 Config 读分辨率并执行一次壁纸更新。
常驻进程请用 run.py → src.app.main。
"""

from __future__ import annotations

from src.arg.arg import Config
from src.resolution_grade import pixel_to_grade
from src.wallpaper_job import build_wallpaper_job


def main() -> None:
    config = Config()
    grade = pixel_to_grade(config.get_download_resolution())
    build_wallpaper_job(
        grade,
        auto_adjust=config.is_auto_adjust_picture(),
        margin_top_percent=config.get_margin_top_percent(),
        margin_bottom_percent=config.get_margin_bottom_percent(),
    )()
