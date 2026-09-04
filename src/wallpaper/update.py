"""壁纸更新触发入口：定时与托盘共用；互斥 + 可选暂停门闩 + 忙时排队跟跑。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

_lock = threading.Lock()
_paused = False
_pause_lock = threading.Lock()
_pending_lock = threading.Lock()
_pending_run = False
_pending_progressive = False
_pending_bypass_pause = False


def is_paused() -> bool:
    with _pause_lock:
        return _paused


def pause() -> None:
    global _paused
    with _pause_lock:
        _paused = True
    logging.info("Wallpaper updates paused (scheduled triggers will be skipped)")


def resume() -> None:
    global _paused
    with _pause_lock:
        _paused = False
    logging.info("Wallpaper updates resumed")


def _queue_follow_up(*, respect_pause: bool, progressive: bool) -> None:
    global _pending_run, _pending_progressive, _pending_bypass_pause
    with _pending_lock:
        _pending_run = True
        _pending_progressive = _pending_progressive or progressive
        _pending_bypass_pause = _pending_bypass_pause or (not respect_pause)


def _take_pending() -> tuple[bool, bool] | None:
    """若有排队则取出并清空；返回 ``(progressive, bypass_pause)``，否则 ``None``。"""
    global _pending_run, _pending_progressive, _pending_bypass_pause
    with _pending_lock:
        if not _pending_run:
            return None
        progressive = _pending_progressive
        bypass_pause = _pending_bypass_pause
        _pending_run = False
        _pending_progressive = False
        _pending_bypass_pause = False
        return progressive, bypass_pause


def _run_pipeline(pipeline: Callable[[], None], *, progressive: bool) -> None:
    if progressive:
        run_progressive = getattr(pipeline, "run_progressive", None)
        if callable(run_progressive):
            run_progressive()
            return
    pipeline()


def run_wallpaper_update(
    pipeline: Callable[[], None],
    *,
    respect_pause: bool = False,
    progressive: bool = False,
) -> bool:
    """空闲时跑一次壁纸更新；已在进行则排队，当前轮结束后跟跑。

    Args:
        pipeline: 组装层注入的零参任务（通常为 ``WallpaperJobRef``）。
        respect_pause: True 时若已暂停则跳过（供定时调度）；手动更新传 False。
        progressive: True 时若 ``pipeline`` 提供 ``run_progressive`` 则走渐进预览。

    Returns:
        True 若本次调用立刻开始执行了流水线；False 若因暂停跳过或仅入队等待跟跑。
    """
    if respect_pause and is_paused():
        logging.info("Wallpaper update paused; ignoring scheduled trigger")
        return False
    if not _lock.acquire(blocking=False):
        _queue_follow_up(respect_pause=respect_pause, progressive=progressive)
        logging.info("Wallpaper update already running; queued follow-up")
        return False
    ran = False
    try:
        while True:
            try:
                _run_pipeline(pipeline, progressive=progressive)
                ran = True
            except Exception:
                logging.exception("Wallpaper update failed")
                raise
            pending = _take_pending()
            if pending is None:
                break
            progressive, bypass_pause = pending
            if not bypass_pause and is_paused():
                logging.info("Wallpaper update paused; dropping queued follow-up")
                break
            logging.info(
                "Running queued wallpaper follow-up (progressive=%s)",
                progressive,
            )
    finally:
        _lock.release()
    return ran
