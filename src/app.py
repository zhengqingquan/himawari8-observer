"""常驻应用启动：日志、CLI、托盘、调度、主线程阻塞。"""

from __future__ import annotations

import logging
import threading

from src.cli.args import Config
from src.event.event import wait_for_shutdown
from src.log.log import init_logging
from src.resolution_grade import pixel_to_grade
from src.timetask import start_scheduler
from src.tray.sysTray import setup_tray_icon
from src.wallpaper.job import WallpaperJobRef


def main() -> None:
    try:
        init_logging()

        config = Config()
        grade = pixel_to_grade(config.get_download_resolution())
        job_ref = WallpaperJobRef(
            grade,
            auto_adjust=config.is_auto_adjust_picture(),
            margin_top_percent=config.get_margin_top_percent(),
            margin_bottom_percent=config.get_margin_bottom_percent(),
            cleanup_after_apply=config.is_cleanup_after_apply(),
        )

        # 托盘与调度共享同一任务引用（托盘可运行中换档）
        threading.Thread(target=lambda: setup_tray_icon(job_ref), daemon=True).start()
        threading.Thread(target=lambda: start_scheduler(job_ref), daemon=True).start()

        wait_for_shutdown()
    except Exception as e:
        logging.error(e)
