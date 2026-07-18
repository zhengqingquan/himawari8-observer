from apscheduler.schedulers.blocking import BlockingScheduler
from src.wallpaper_update import run_wallpaper_update
import sys
from collections.abc import Callable
from src.metadata.soft_config import DOWNLOAD_INTERVAL_TIME


def stat_time_tast(pipeline: Callable[[], None]):
    scheduler = BlockingScheduler()

    # 间隔触发；不设 next_run_time=now，避免启动时立刻下载更新
    scheduler.add_job(
        lambda: run_wallpaper_update(pipeline=pipeline, respect_pause=True),
        "interval",
        seconds=DOWNLOAD_INTERVAL_TIME,
    )

    # 也可以添加其他类型的任务，比如每天在特定时间执行
    # scheduler.add_job(job, 'cron', hour=10, minute=30)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
        sys.exit(0)
