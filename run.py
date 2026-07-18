import threading
import logging
from src.log.log import log_init
from src.arg.arg import Config
from src.resolution_grade import pixel_to_grade
from src.wallpaper_job import WallpaperJobRef
from src.UI.sysTray import setup_tray_icon
from src.timetask import stat_time_tast
from src.event.event import wait_sys

if __name__ == "__main__":
    try:
        # 初始化日志
        log_init()

        # 处理参数命令和初始化程序配置
        config = Config()
        grade = pixel_to_grade(config.get_download_resolution())
        job_ref = WallpaperJobRef(
            grade, auto_adjust=config.is_auto_adjust_picture()
        )

        # 托盘与调度共享同一任务引用（托盘可运行中换档）
        tray_thread = threading.Thread(
            target=lambda: setup_tray_icon(job_ref), daemon=True
        )
        tray_thread.start()

        scheduler_thread = threading.Thread(
            target=lambda: stat_time_tast(job_ref), daemon=True
        )
        scheduler_thread.start()

        # 等待停止事件
        wait_sys()
    except Exception as e:
        logging.error(e)
