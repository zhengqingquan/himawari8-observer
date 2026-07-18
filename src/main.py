"""
main.py

主函数入口：把 Config 分辨率接到壁纸更新流水线。
"""

# !/usr/bin/env python

from __future__ import annotations

from collections.abc import Callable

from src.arg.arg import Config
from src.resolution_grade import pixel_to_grade
from src.wallpaper_pipeline import run_wallpaper_pipeline


def main(
    *,
    run_pipeline: Callable[..., None] | None = None,
    get_resolution_pixel: Callable[[], int] | None = None,
) -> None:
    pipeline = run_pipeline or run_wallpaper_pipeline
    read_pixel = get_resolution_pixel or (lambda: Config().get_download_resolution())
    grade = pixel_to_grade(read_pixel())
    pipeline(resolution_grade=grade)
