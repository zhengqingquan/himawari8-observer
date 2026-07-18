"""
main.py

一次性入口：从 Config 读分辨率并执行一次壁纸更新。
常驻进程请在 run.py 用 build_wallpaper_job 冻结档位后注入。
"""

# !/usr/bin/env python

from __future__ import annotations

from src.arg.arg import Config
from src.resolution_grade import pixel_to_grade
from src.wallpaper_job import build_wallpaper_job


def main() -> None:
    grade = pixel_to_grade(Config().get_download_resolution())
    build_wallpaper_job(grade)()
