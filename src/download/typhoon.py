"""台风目标区：从 NICT D531108 JSON 读取中心点。"""

from __future__ import annotations

import logging
from time import strftime, struct_time
from typing import Any

import requests

_TYPHOON_JSON_TMPL = (
    "https://himawari8.nict.go.jp/json/D531108/{year}/{month}/{day}/{hhmmss}.json"
)
_REQUEST_TIMEOUT_SEC = (5, 14)


def typhoon_json_url(observation_time: struct_time) -> str:
    """按观测时间拼装 D531108 JSON URL。"""
    return _TYPHOON_JSON_TMPL.format(
        year=strftime("%Y", observation_time),
        month=strftime("%m", observation_time),
        day=strftime("%d", observation_time),
        hhmmss=strftime("%H%M%S", observation_time),
    )


def fetch_typhoon_center(
    observation_time: struct_time,
    *,
    session: requests.Session | None = None,
) -> tuple[float, float] | None:
    """拉取台风目标区中心 ``(lat, lon)``；无台风或失败时返回 ``None``。

    Args:
        observation_time: 与全盘影像对齐的 UTC 观测时间。
        session: 可选可复用会话。

    Returns:
        ``type == "TY"`` 且含合法 ``center`` 时返回 ``(latitude, longitude)``；否则 ``None``。
    """
    url = typhoon_json_url(observation_time)
    client = session or requests
    proxies = {"http": None, "https": None}
    try:
        response = client.get(url, timeout=_REQUEST_TIMEOUT_SEC, proxies=proxies, verify=True)
        if response.status_code == 404:
            logging.info("No typhoon target JSON for %s", strftime("%Y-%m-%d %H:%M:%S", observation_time))
            return None
        response.raise_for_status()
        payload: Any = response.json()
    except (OSError, ValueError, requests.RequestException):
        logging.warning("Failed to fetch typhoon target JSON: %s", url, exc_info=True)
        return None

    if not isinstance(payload, dict):
        logging.info("Typhoon JSON is not an object: %s", url)
        return None
    if payload.get("type") != "TY":
        logging.info("Typhoon JSON type is not TY (%r); skipping marker", payload.get("type"))
        return None
    center = payload.get("center")
    if (
        not isinstance(center, (list, tuple))
        or len(center) != 2
        or not all(isinstance(v, (int, float)) for v in center)
    ):
        logging.info("Typhoon JSON missing valid center: %s", url)
        return None
    lat, lon = float(center[0]), float(center[1])
    logging.info("Typhoon center: lat=%s lon=%s", lat, lon)
    return lat, lon
