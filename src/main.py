"""一次性入口：从 Config 读参数并执行一次壁纸更新。

常驻进程请用 ``run.py`` → ``src.app.main``。
"""

from __future__ import annotations

from src.cli.args import Config
from src.resolution_grade import pixel_to_grade
from src.wallpaper.job import build_wallpaper_job


def main() -> None:
    """读取 CLI 配置并同步跑完一轮壁纸流水线。"""
    config = Config()
    grade = pixel_to_grade(config.get_download_resolution())
    build_wallpaper_job(
        grade,
        auto_adjust=config.is_auto_adjust_picture(),
        margin_top_percent=config.get_margin_top_percent(),
        margin_bottom_percent=config.get_margin_bottom_percent(),
        cleanup_after_apply=config.is_cleanup_after_apply(),
    )()


if __name__ == "__main__":
    main()
