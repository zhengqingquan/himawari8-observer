"""壁纸更新触发入口：定时与托盘共用，互斥保证同时只有一次流水线。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from src.main import main

_lock = threading.Lock()


def run_wallpaper_update(pipeline: Callable[[], None] | None = None) -> bool:
    """空闲时跑一次壁纸更新；已在进行则跳过。

    Returns:
        True 若本次执行了流水线；False 若因互斥被跳过。
    """
    job = pipeline if pipeline is not None else main
    if not _lock.acquire(blocking=False):
        logging.info("壁纸更新已在进行，忽略本次触发")
        return False
    try:
        job()
        return True
    finally:
        _lock.release()
