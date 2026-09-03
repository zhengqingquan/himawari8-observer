"""瓦片下载的并发实现细节（线程池 + Session/retry）。"""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable, Mapping
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

DownloadOne = Callable[[str, Any], Any]


def _build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def download_file(url, path, *, session: requests.Session | None = None):
    """下载单张瓦片到 path。

    Args:
        url: 瓦片 URL。
        path: 本地保存路径。
        session: 可选共用 Session（含 retry）。

    Returns:
        URL 路径最后一段文件名。
    """
    proxies = {"http": None, "https": None}
    client = session or requests
    with client.get(url, stream=True, verify=True, proxies=proxies, timeout=(5, 14)) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return url.split("/")[-1]


def download_files(
    urls: Mapping[str, Any],
    *,
    download_one: DownloadOne | None = None,
    max_workers: int = 16,
) -> None:
    """使用线程池下载 urls（值为 ``[path, status]``）。成功则 status=1。

    Args:
        urls: url → ``[path, status]`` 映射。
        download_one: 可选单瓦片下载回调 ``(url, path)``；默认走 Session/retry。
        max_workers: 线程池大小。
    """
    session = None if download_one is not None else _build_session()

    def default_one(url, path):
        return download_file(url, path, session=session)

    one = download_one or default_one
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(one, url, entry[0]): (url, entry) for url, entry in urls.items()
        }
        for future in concurrent.futures.as_completed(future_to_entry):
            url, entry = future_to_entry[future]
            try:
                future.result()
                entry[1] = 1
                logging.info("Downloaded tile: %s", url)
            except Exception as exc:
                logging.warning("Failed to download tile %s: %s", url, exc)
