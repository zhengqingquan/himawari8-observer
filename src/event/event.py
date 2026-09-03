"""进程保活：主线程等待退出信号。"""

from __future__ import annotations

import threading

stop_event = threading.Event()


def end_main_sys() -> None:
    """通知主线程退出。"""
    stop_event.set()


def wait_sys() -> None:
    """阻塞直至 ``end_main_sys`` 被调用。"""
    stop_event.wait()
