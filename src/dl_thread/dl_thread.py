"""
创建下载的线程
"""

from __future__ import annotations

import concurrent.futures
from collections.abc import Callable, Mapping
from typing import Any

import requests

# 假设这是你要下载的文件的URL列表（本地演示用）
file_urls = [
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_0.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_1.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_2.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_3.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_0.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_1.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_2.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_3.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_2_0.png",
    "https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_2_1.png",
]

DownloadOne = Callable[[str, Any], Any]


def download_file(url, path):
    """下载单张瓦片到 path。"""
    local_filename = url.split("/")[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


def download_files(
    urls: Mapping[str, Any],
    *,
    download_one: DownloadOne | None = None,
    max_workers: int = 16,
) -> None:
    """使用线程池下载 urls（值为 [path, status]）。单张下载可注入。"""
    one = download_one or download_file
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(one, url, path[0]): (url, path[0]) for url, path in urls.items()
        }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
                print(f"{url} 下载完成")
            except Exception as exc:
                print(f"{url} 下载时出错: {exc}")
