"""观测时间：Session 与 latest.json。"""

from __future__ import annotations

import json
import logging
from time import strptime

import requests


def dl_init() -> requests.Session:
    """创建可复用的 requests 会话。

    Returns:
        新的 Session 实例。
    """
    return requests.Session()


def get_last_time(request: requests.Session):
    """从 NICT latest.json 读取最新观测时间。

    Args:
        request: 可复用的 requests 会话。

    Returns:
        观测时间（struct_time，对应 ``%Y-%m-%d %H:%M:%S``）。
    """
    proxies = {"http": None, "https": None}
    verify = True
    stream = True
    url = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"
    response = request.get(url, verify=verify, proxies=proxies, stream=stream)
    latest_json = response.content
    logging.debug(latest_json)
    date_str = json.loads(latest_json.decode("utf-8"))["date"]
    latest_time = strptime(date_str, "%Y-%m-%d %H:%M:%S")
    logging.info("当前时间为：" + date_str)
    return latest_time
