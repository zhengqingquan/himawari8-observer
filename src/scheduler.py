"""定时调度：按配置间隔触发壁纸更新。"""

from __future__ import annotations

import datetime
import logging
import sys
from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler

from src.metadata.app_config import DOWNLOAD_INTERVAL_TIME
from src.wallpaper.update import run_wallpaper_update

_SCHEDULER_JOB_ID = "wallpaper_tick"
_scheduler: BlockingScheduler | None = None


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


def reschedule_interval(seconds: int) -> None:
    """运行中调整间隔；调度器未启动时 no-op。下一拍起生效，不立刻 tick。"""
    if seconds <= 0:
        logging.warning("Ignoring non-positive schedule interval: %s", seconds)
        return
    scheduler = _scheduler
    if scheduler is None:
        logging.debug("Scheduler not started; skip reschedule to %ss", seconds)
        return
    try:
        scheduler.reschedule_job(
            _SCHEDULER_JOB_ID,
            trigger="interval",
            seconds=seconds,
        )
    except Exception:
        logging.exception("Failed to reschedule wallpaper tick to %ss", seconds)
        return
    logging.info("Wallpaper schedule interval set to %ss", seconds)


def start_scheduler(
    pipeline: Callable[[], None],
    *,
    interval_seconds: int = DOWNLOAD_INTERVAL_TIME,
) -> None:
    """阻塞运行间隔调度；启动后立即执行一次，之后按 ``interval_seconds`` 周期触发。

    进程内第一次触发使用渐进分辨率；后续周期触发直接跑目标档。

    Args:
        pipeline: 零参壁纸任务（通常为 WallpaperJobRef）。
        interval_seconds: 周期秒数；默认 ``DOWNLOAD_INTERVAL_TIME``。
    """
    global _scheduler
    seconds = interval_seconds if interval_seconds > 0 else DOWNLOAD_INTERVAL_TIME
    tick = build_scheduler_tick(pipeline)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        tick,
        "interval",
        seconds=seconds,
        id=_SCHEDULER_JOB_ID,
        next_run_time=datetime.datetime.now(),
    )
    _scheduler = scheduler
    logging.info("Scheduler started with interval %ss", seconds)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler shutting down")
        scheduler.shutdown(wait=False)
        _scheduler = None
        sys.exit(0)
