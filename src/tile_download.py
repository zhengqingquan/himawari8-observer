"""瓦片下载：pipeline 与遗留调用方共用的唯一 live interface。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.cls.Pic import Pic
from src.dl_thread.dl_thread import download_files

DownloadFiles = Callable[..., None]


def download_tiles(
    pic: Pic,
    *,
    download_files_impl: DownloadFiles | None = None,
    **kwargs: Any,
) -> None:
    """下载 pic.dic 中的全部瓦片（线程池 + Session/retry/状态位）。"""
    impl = download_files_impl or download_files
    impl(pic.dic, **kwargs)
