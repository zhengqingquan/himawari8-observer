"""
main.py

主函数入口：转发到壁纸更新流水线。
"""

# !/usr/bin/env python

from src.wallpaper_pipeline import run_wallpaper_pipeline


def main():
    run_wallpaper_pipeline()
