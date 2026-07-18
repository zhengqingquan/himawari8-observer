from apscheduler.schedulers.blocking import BlockingScheduler
from src.wallpaper_update import run_wallpaper_update
import sys
import datetime
from collections.abc import Callable
from src.metadata.soft_config import DOWNLOAD_INTERVAL_TIME


def stat_time_tast(pipeline: Callable[[], None]):
    scheduler = BlockingScheduler()

    # 添加一个每隔一段时间执行一次
    scheduler.add_job(
        lambda: run_wallpaper_update(pipeline=pipeline),
        "interval",
        seconds=DOWNLOAD_INTERVAL_TIME,
        next_run_time=datetime.datetime.now(),
    )

    # 也可以添加其他类型的任务，比如每天在特定时间执行
    # scheduler.add_job(job, 'cron', hour=10, minute=30)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
        sys.exit(0)
