"""瓦片下载的并发实现细节（线程池 + Session/retry）。"""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.pic import TileSlot

DownloadOne = Callable[[str, Any], Any]

# 首轮之外，对仍失败的瓦片再补下的轮数。
_DEFAULT_RETRY_ROUNDS = 2
_PART_SUFFIX = ".part"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _build_session(*, pool_size: int = 16) -> requests.Session:
    """创建带 retry 的 Session；连接池大小与并发线程数对齐。"""
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download_file(url, path, *, session: requests.Session | None = None):
    """下载单张瓦片到 path（先写 ``.part`` 再原子替换，避免半写入被当成成品）。

    Args:
        url: 瓦片 URL。
        path: 本地保存路径。
        session: 可选共用 Session（含 retry）。

    Returns:
        URL 路径最后一段文件名。
    """
    proxies = {"http": None, "https": None}
    client = session or requests
    dest = Path(path)
    part = dest.with_name(dest.name + _PART_SUFFIX)
    try:
        with client.get(url, stream=True, verify=True, proxies=proxies, timeout=(5, 14)) as r:
            r.raise_for_status()
            with open(part, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        part.replace(dest)
    except Exception:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            logging.debug("Failed to remove partial tile: %s", part, exc_info=True)
        raise
    return url.split("/")[-1]


def _existing_tile_ok(path: Any) -> bool:
    """本地瓦片已存在、非空且具有 PNG 文件头时可跳过下载。"""
    try:
        file_path = Path(path)
        if not file_path.is_file():
            return False
        if file_path.stat().st_size < len(_PNG_MAGIC):
            return False
        with file_path.open("rb") as f:
            return f.read(len(_PNG_MAGIC)) == _PNG_MAGIC
    except OSError:
        return False


def _run_download_round(
    batch: Mapping[str, TileSlot],
    *,
    download_one: DownloadOne,
    max_workers: int,
    round_label: str,
) -> None:
    """并发下载一批瓦片；成功则 ``done=True``，失败保持 ``False``。"""
    if not batch:
        return
    ok_count = 0
    fail_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(download_one, url, entry.path): (url, entry)
            for url, entry in batch.items()
        }
        for future in concurrent.futures.as_completed(future_to_entry):
            url, entry = future_to_entry[future]
            try:
                future.result()
                entry.done = True
                ok_count += 1
                logging.debug("Downloaded tile (%s): %s", round_label, url)
            except Exception as exc:
                fail_count += 1
                logging.warning(
                    "Failed to download tile (%s) %s: %s",
                    round_label,
                    url,
                    exc,
                )
    logging.info(
        "Tile download %s: %s ok, %s failed (of %s)",
        round_label,
        ok_count,
        fail_count,
        ok_count + fail_count,
    )


def download_files(
    urls: Mapping[str, TileSlot],
    *,
    download_one: DownloadOne | None = None,
    max_workers: int = 16,
    retry_rounds: int = _DEFAULT_RETRY_ROUNDS,
) -> None:
    """使用线程池下载 urls（值为 ``TileSlot``）。成功则 ``done=True``。

    已存在且带 PNG 头的本地文件会直接标记成功并跳过网络请求。
    首轮结束后，对仍失败的瓦片再补下最多 ``retry_rounds`` 轮。

    Args:
        urls: url → ``TileSlot`` 映射。
        download_one: 可选单瓦片下载回调 ``(url, path)``；默认走 Session/retry。
        max_workers: 线程池大小（同时作为 Session 连接池上限）。
        retry_rounds: 首轮之外的失败补下轮数；``0`` 表示不补下。
    """
    pending: dict[str, TileSlot] = {}
    skipped = 0
    for url, entry in urls.items():
        if _existing_tile_ok(entry.path):
            entry.done = True
            skipped += 1
            logging.debug("Skipped existing tile: %s", entry.path)
            continue
        pending[url] = entry

    if skipped:
        logging.info("Skipped %s existing tile(s)", skipped)

    if not pending:
        return

    session = None if download_one is not None else _build_session(pool_size=max_workers)

    def default_one(url, path):
        return download_file(url, path, session=session)

    one = download_one or default_one
    rounds = max(0, int(retry_rounds))

    _run_download_round(
        pending,
        download_one=one,
        max_workers=max_workers,
        round_label="pass-1",
    )

    for retry_index in range(1, rounds + 1):
        failed = {url: entry for url, entry in pending.items() if not entry.done}
        if not failed:
            break
        logging.info(
            "Retrying %s failed tile(s), round %s/%s",
            len(failed),
            retry_index,
            rounds,
        )
        _run_download_round(
            failed,
            download_one=one,
            max_workers=max_workers,
            round_label=f"retry-{retry_index}",
        )
