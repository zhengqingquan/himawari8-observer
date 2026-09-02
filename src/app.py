"""常驻应用启动：日志、CLI、托盘、调度、主线程阻塞。"""

from __future__ import annotations

import logging
import threading

from src.arg.arg import Config
from src.event.event import wait_sys
from src.log.log import log_init
from src.resolution_grade import pixel_to_grade
from src.timetask import stat_time_tast
from src.UI.sysTray import setup_tray_icon
from src.wallpaper_job import WallpaperJobRef


def main() -> None:
    try:
        log_init()

        config = Config()
        grade = pixel_to_grade(config.get_download_resolution())
        job_ref = WallpaperJobRef(
            grade, auto_adjust=config.is_auto_adjust_picture()
        )

        # 托盘与调度共享同一任务引用（托盘可运行中换档）
        threading.Thread(
            target=lambda: setup_tray_icon(job_ref), daemon=True
        ).start()
        threading.Thread(
            target=lambda: stat_time_tast(job_ref), daemon=True
        ).start()

        wait_sys()
    except Exception as e:
        logging.error(e)
