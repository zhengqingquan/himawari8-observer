"""进程保活：主线程等待退出信号。"""

from __future__ import annotations

import threading

stop_event = threading.Event()


def request_shutdown() -> None:
    """通知主线程退出。"""
    stop_event.set()


def wait_for_shutdown() -> None:
    """阻塞直至 ``request_shutdown`` 被调用。"""
    stop_event.wait()
