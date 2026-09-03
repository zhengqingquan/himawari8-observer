"""观测时间：Session 与 latest.json。"""

from __future__ import annotations

import json
import logging
from time import strptime

import requests

_LATEST_JSON_URL = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"


def create_session() -> requests.Session:
    """创建可复用的 requests 会话。

    Returns:
        新的 Session 实例。
    """
    return requests.Session()


def fetch_observation_time(session: requests.Session):
    """从 NICT latest.json 读取最新观测时间。

    Args:
        session: 可复用的 requests 会话。

    Returns:
        观测时间（struct_time，对应 ``%Y-%m-%d %H:%M:%S``）。
    """
    proxies = {"http": None, "https": None}
    try:
        response = session.get(
            _LATEST_JSON_URL,
            verify=True,
            proxies=proxies,
            stream=True,
            timeout=(5, 14),
        )
        response.raise_for_status()
        latest_json = response.content
        logging.debug("latest.json raw response: %s", latest_json)
        date_str = json.loads(latest_json.decode("utf-8"))["date"]
        latest_time = strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        logging.exception("Failed to fetch observation time from %s", _LATEST_JSON_URL)
        raise
    logging.info("Latest observation time: %s", date_str)
    return latest_time
