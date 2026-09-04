"""太阳直射点：由 UTC 观测时间本地计算（NOAA 近似，无网络）。"""

from __future__ import annotations

import math
from time import struct_time


def _julian_day_utc(observation_time: struct_time) -> float:
    """UTC ``struct_time`` → 儒略日（含日分数）。"""
    year = observation_time.tm_year
    month = observation_time.tm_mon
    day = observation_time.tm_mday
    hour = observation_time.tm_hour
    minute = observation_time.tm_min
    second = observation_time.tm_sec
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd0 = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd0 + (hour + minute / 60.0 + second / 3600.0) / 24.0


def _normalize_lon_deg(lon: float) -> float:
    """经度规范到 ``[-180, 180]``。"""
    lon = (lon + 180.0) % 360.0 - 180.0
    if lon == -180.0:
        return 180.0
    return lon


def subsolar_latlon(observation_time: struct_time) -> tuple[float, float]:
    """按 UTC 观测时间计算太阳直射点 ``(lat, lon)``（度，北正 / 东正）。

    使用 NOAA Solar Calculator 常用近似（儒略世纪 → 赤纬 + 均时差），
    精度对本壁纸标注足够（约 0.1° 量级），无需外网或天文库。
    """
    jd = _julian_day_utc(observation_time)
    t = (jd - 2451545.0) / 36525.0

    # 几何平黄经、平近点角（度）
    l0 = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360.0
    m_deg = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    m_rad = math.radians(m_deg)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    # 中心差 → 真黄经
    c = (
        math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t))
        + math.sin(2.0 * m_rad) * (0.019993 - 0.000101 * t)
        + math.sin(3.0 * m_rad) * 0.000289
    )
    true_long = l0 + c
    omega = 125.04 - 1934.136 * t
    lambda_app = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))

    # 黄赤交角
    epsilon0 = (
        23.0
        + (
            26.0
            + (
                21.448
                - t * (46.8150 + t * (0.00059 - t * 0.001813))
            )
            / 60.0
        )
        / 60.0
    )
    epsilon = epsilon0 + 0.00256 * math.cos(math.radians(omega))
    eps_rad = math.radians(epsilon)
    lambda_rad = math.radians(lambda_app)

    # 赤纬 = 直射点纬度
    sin_decl = math.sin(eps_rad) * math.sin(lambda_rad)
    sin_decl = max(-1.0, min(1.0, sin_decl))
    lat = math.degrees(math.asin(sin_decl))

    # 均时差（分钟）→ 直射点经度
    y = math.tan(eps_rad / 2.0) ** 2
    l0_rad = math.radians(l0)
    eq_time = 4.0 * math.degrees(
        y * math.sin(2.0 * l0_rad)
        - 2.0 * e * math.sin(m_rad)
        + 4.0 * e * y * math.sin(m_rad) * math.cos(2.0 * l0_rad)
        - 0.5 * y * y * math.sin(4.0 * l0_rad)
        - 1.25 * e * e * math.sin(2.0 * m_rad)
    )
    ut_hours = (
        observation_time.tm_hour
        + observation_time.tm_min / 60.0
        + observation_time.tm_sec / 3600.0
    )
    lon = _normalize_lon_deg(-15.0 * (ut_hours - 12.0) - eq_time / 4.0)
    return lat, lon
