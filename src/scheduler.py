"""定时调度：按配置间隔触发壁纸更新。"""

from __future__ import annotations

import datetime
import logging
import sys
from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler

from src.metadata.app_config import DOWNLOAD_INTERVAL_TIME
from src.wallpaper.update import run_wallpaper_update


def build_scheduler_tick(pipeline: Callable[[], None]) -> Callable[[], None]:
    """构造调度回调：进程内第一次 ``progressive=True``，之后为 ``False``。"""
    first_run = {"progressive": True}

    def tick() -> None:
        progressive = first_run["progressive"]
        first_run["progressive"] = False
        run_wallpaper_update(
            pipeline=pipeline,
            respect_pause=True,
            progressive=progressive,
        )

    return tick


def start_scheduler(pipeline: Callable[[], None]) -> None:
    """阻塞运行间隔调度；启动后立即执行一次，之后按 ``DOWNLOAD_INTERVAL_TIME`` 周期触发。

    进程内第一次触发使用渐进分辨率；后续周期触发直接跑目标档。

    Args:
        pipeline: 零参壁纸任务（通常为 WallpaperJobRef）。
    """
    tick = build_scheduler_tick(pipeline)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        tick,
        "interval",
        seconds=DOWNLOAD_INTERVAL_TIME,
        next_run_time=datetime.datetime.now(),
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler shutting down")
        scheduler.shutdown(wait=False)
        sys.exit(0)
