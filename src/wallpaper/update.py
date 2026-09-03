"""壁纸更新触发入口：定时与托盘共用；互斥 + 可选暂停门闩。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

_lock = threading.Lock()
_paused = False
_pause_lock = threading.Lock()


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


def run_wallpaper_update(
    pipeline: Callable[[], None],
    *,
    respect_pause: bool = False,
) -> bool:
    """空闲时跑一次壁纸更新；已在进行则跳过。

    Args:
        pipeline: 组装层注入的零参任务。
        respect_pause: True 时若已暂停则跳过（供定时调度）；手动更新传 False。

    Returns:
        True 若本次执行了流水线；False 若因互斥或暂停被跳过。
    """
    if respect_pause and is_paused():
        logging.info("Wallpaper update paused; ignoring scheduled trigger")
        return False
    if not _lock.acquire(blocking=False):
        logging.info("Wallpaper update already running; ignoring trigger")
        return False
    try:
        pipeline()
        return True
    except Exception:
        logging.exception("Wallpaper update failed")
        raise
    finally:
        _lock.release()
