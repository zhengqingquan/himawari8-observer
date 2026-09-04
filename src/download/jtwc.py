"""JTWC 西太显著热带天气通报：解析 INVEST 扰动位置。"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

_ABPW_URL = "https://tgftp.nws.noaa.gov/data/raw/ab/abpw10.pgtw..txt"
_REQUEST_TIMEOUT_SEC = (5, 20)

# INVEST 97W ... NOW LOCATED NEAR 19.2N 138.3E  （或单次 LOCATED NEAR）
_INVEST_ID_RE = re.compile(r"\bINVEST\s+(\d{1,2}[A-Z])\b", re.IGNORECASE)
_LATLON_RE = re.compile(
    r"(?:NOW\s+)?LOCATED\s+NEAR\s+(\d+(?:\.\d+)?)\s*([NS])\s+(\d+(?:\.\d+)?)\s*([EW])",
    re.IGNORECASE,
)


def _hemisphere_lat(value: float, hemi: str) -> float:
    lat = float(value)
    if hemi.upper() == "S":
        lat = -lat
    return lat


def _hemisphere_lon(value: float, hemi: str) -> float:
    lon = float(value)
    if hemi.upper() == "W":
        lon = -lon
    return lon


def parse_jtwc_invests(text: str) -> list[dict[str, Any]]:
    """从 ABPW 正文解析 INVEST 列表 ``[{id, lat, lon}, ...]``。

    只认 ``INVEST xxW`` 扰动，不解析正式 TROPICAL STORM / TYPHOON 段落。
    每个 INVEST 取其后文中**最后一次** ``(NOW )LOCATED NEAR`` 坐标。
    """
    if not text or not text.strip():
        return []

    # 只看西太节（至 SOUTH PACIFIC / 文末）
    upper = text.upper()
    start = upper.find("WESTERN NORTH PACIFIC")
    body = text[start:] if start >= 0 else text
    end_markers = (
        "\n2. SOUTH PACIFIC",
        "\n2.SOUTH PACIFIC",
        "\nSOUTH PACIFIC AREA",
    )
    end = len(body)
    for marker in end_markers:
        idx = body.upper().find(marker.upper())
        if idx >= 0:
            end = min(end, idx)
    section = body[:end]

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in _INVEST_ID_RE.finditer(section):
        invest_id = match.group(1).upper()
        if invest_id in seen:
            continue
        # 从该 INVEST 出现处向前搜到下一个 INVEST 或节末
        chunk_start = match.start()
        next_invest = _INVEST_ID_RE.search(section, match.end())
        chunk_end = next_invest.start() if next_invest else len(section)
        chunk = section[chunk_start:chunk_end]
        latlon_matches = list(_LATLON_RE.finditer(chunk))
        if not latlon_matches:
            logging.info("JTWC INVEST %s has no LOCATED NEAR lat/lon; skipping", invest_id)
            continue
        last = latlon_matches[-1]
        lat = _hemisphere_lat(float(last.group(1)), last.group(2))
        lon = _hemisphere_lon(float(last.group(3)), last.group(4))
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            continue
        seen.add(invest_id)
        results.append({"id": invest_id, "lat": lat, "lon": lon})
    return results


def fetch_jtwc_invests(
    *,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """拉取 ABPW 并解析 INVEST；失败返回空列表。"""
    client = session or requests
    proxies = {"http": None, "https": None}
    try:
        response = client.get(
            _ABPW_URL,
            timeout=_REQUEST_TIMEOUT_SEC,
            proxies=proxies,
            verify=True,
        )
        response.raise_for_status()
        text = response.text
    except (OSError, ValueError, requests.RequestException):
        logging.warning("Failed to fetch JTWC ABPW: %s", _ABPW_URL, exc_info=True)
        return []

    invests = parse_jtwc_invests(text)
    if invests:
        logging.info(
            "JTWC invests: %s",
            ", ".join(f"{item['id']}@{item['lat']},{item['lon']}" for item in invests),
        )
    else:
        logging.info("JTWC ABPW: no INVEST positions parsed")
    return invests
