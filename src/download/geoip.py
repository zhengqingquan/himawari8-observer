"""IP 粗定位：从免费 HTTPS 接口读取经纬度。"""

from __future__ import annotations

import logging
from typing import Any

import requests

_IPWHO_URL = "https://ipwho.is/"
_REQUEST_TIMEOUT_SEC = (5, 14)


def fetch_ip_latlon(
    *,
    session: requests.Session | None = None,
) -> tuple[float, float] | None:
    """经 IP 粗定位返回 ``(lat, lon)``；失败时返回 ``None``。

    Args:
        session: 可选可复用会话。

    Returns:
        成功时为纬度、经度（度）；失败或字段非法时 ``None``。
    """
    client = session or requests
    proxies = {"http": None, "https": None}
    try:
        response = client.get(
            _IPWHO_URL,
            timeout=_REQUEST_TIMEOUT_SEC,
            proxies=proxies,
            verify=True,
        )
        response.raise_for_status()
        payload: Any = response.json()
    except (OSError, ValueError, requests.RequestException):
        logging.warning("Failed to fetch IP geolocation: %s", _IPWHO_URL, exc_info=True)
        return None

    if not isinstance(payload, dict):
        logging.info("IP geolocation response is not an object")
        return None
    if payload.get("success") is False:
        logging.info("IP geolocation reported failure: %r", payload.get("message"))
        return None
    lat = payload.get("latitude")
    lon = payload.get("longitude")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        logging.info("IP geolocation missing valid latitude/longitude")
        return None
    lat_f, lon_f = float(lat), float(lon)
    if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
        logging.info("IP geolocation out of range: lat=%s lon=%s", lat_f, lon_f)
        return None
    logging.info("IP geolocation: lat=%s lon=%s", lat_f, lon_f)
    return lat_f, lon_f
