"""瓦片下载：pipeline 与遗留调用方共用的唯一 live interface。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.download.pool import download_files
from src.pic.pic import Pic

DownloadFiles = Callable[..., None]


def download_tiles(
    pic: Pic,
    *,
    download_files_impl: DownloadFiles | None = None,
    **kwargs: Any,
) -> None:
    """下载 ``pic.tiles`` 中的全部瓦片（线程池 + Session/retry/状态位）。

    Args:
        pic: 等分瓦片图实例。
        download_files_impl: 可注入的批量下载实现；默认 ``download_files``。
        **kwargs: 转发给批量下载实现。
    """
    impl = download_files_impl or download_files
    impl(pic.tiles, **kwargs)
