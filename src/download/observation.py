"""观测时间：Session、latest.json、按本地钟点取昨日帧。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from time import strftime, strptime, struct_time

import requests

_LATEST_JSON_URL = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"
_OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"
_FULL_DISK_INTERVAL_MINUTES = 10


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
        latest_time = strptime(date_str, _OBS_TIME_FMT)
    except Exception:
        logging.exception("Failed to fetch observation time from %s", _LATEST_JSON_URL)
        raise
    logging.info("Latest observation time: %s", date_str)
    return latest_time


def observation_time_yesterday_local(
    *,
    now: datetime | None = None,
) -> struct_time:
    """按本机当前钟点取「昨日同时刻」对应的 UTC 观测帧。

    步骤：本地 now → 减 1 天 → 换算 UTC → 向下取整到 10 分钟（秒归零）。

    Args:
        now: 可注入的当前时刻；naive 视为本地时区，aware 按其 ``tzinfo``；
            默认 ``datetime.now().astimezone()``。

    Returns:
        UTC 观测时间（struct_time，对应 ``%Y-%m-%d %H:%M:%S``）。
    """
    if now is None:
        local_now = datetime.now().astimezone()
    elif now.tzinfo is None:
        local_now = now.astimezone()
    else:
        local_now = now

    local_yesterday = local_now - timedelta(days=1)
    utc_dt = local_yesterday.astimezone(timezone.utc)
    floored_minute = (utc_dt.minute // _FULL_DISK_INTERVAL_MINUTES) * _FULL_DISK_INTERVAL_MINUTES
    utc_slot = utc_dt.replace(minute=floored_minute, second=0, microsecond=0)
    result = utc_slot.timetuple()
    logging.info(
        "Yesterday-local observation: local=%s -> utc_slot=%s",
        local_yesterday.strftime(_OBS_TIME_FMT),
        strftime(_OBS_TIME_FMT, result),
    )
    return result
