"""太阳位置与葵花视角耀斑：由 UTC 观测时间本地计算（无网络）。"""

from __future__ import annotations

import math
from time import struct_time

# 与 ``compose.geo`` 全盘投影星下点经度一致（Himawari-8/9）。
_HIMAWARI_SUB_SATELLITE_LON_DEG = 140.7


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


def _latlon_to_unit(lat_deg: float, lon_deg: float) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    cos_lat = math.cos(lat)
    return (cos_lat * math.cos(lon), cos_lat * math.sin(lon), math.sin(lat))


def _unit_to_latlon(x: float, y: float, z: float) -> tuple[float, float]:
    hyp = math.hypot(x, y)
    lat = math.degrees(math.atan2(z, hyp))
    lon = _normalize_lon_deg(math.degrees(math.atan2(y, x)))
    return lat, lon


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
    epsilon0 = 23.0 + (26.0 + (21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
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
        observation_time.tm_hour + observation_time.tm_min / 60.0 + observation_time.tm_sec / 3600.0
    )
    lon = _normalize_lon_deg(-15.0 * (ut_hours - 12.0) - eq_time / 4.0)
    return lat, lon


def is_sunlit(
    lat_deg: float,
    lon_deg: float,
    observation_time: struct_time,
) -> bool:
    """几何昼侧判定：点与太阳直射点单位矢量点积 ``> 0``（太阳高度角 > 0）。"""
    sun_lat, sun_lon = subsolar_latlon(observation_time)
    sx, sy, sz = _latlon_to_unit(sun_lat, sun_lon)
    px, py, pz = _latlon_to_unit(lat_deg, lon_deg)
    return (sx * px + sy * py + sz * pz) > 0.0


def _basis_perpendicular_to(
    nx: float, ny: float, nz: float
) -> tuple[float, float, float, float, float, float]:
    """单位矢量 ``n`` 的右手正交基底 ``(u, v)``，满足 ``u×v`` 平行 ``n``。"""
    if abs(nx) < 0.9:
        ax, ay, az = 1.0, 0.0, 0.0
    else:
        ax, ay, az = 0.0, 1.0, 0.0
    ux = ay * nz - az * ny
    uy = az * nx - ax * nz
    uz = ax * ny - ay * nx
    un = math.sqrt(ux * ux + uy * uy + uz * uz)
    if un <= 0.0:
        return 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
    ux, uy, uz = ux / un, uy / un, uz / un
    vx = ny * uz - nz * uy
    vy = nz * ux - nx * uz
    vz = nx * uy - ny * ux
    return ux, uy, uz, vx, vy, vz


def points_on_solar_mu_circle(
    observation_time: struct_time,
    mu: float,
    *,
    sample_count: int = 720,
) -> list[tuple[float, float]]:
    """太阳方向点积为 ``mu`` 的大圆采样点 ``(lat, lon)``（度）。

    ``mu = 0`` 为几何晨昏线；``|mu| > 1`` 无解返回空列表。
    """
    if sample_count < 3 or abs(mu) > 1.0:
        return []
    sun_lat, sun_lon = subsolar_latlon(observation_time)
    sx, sy, sz = _latlon_to_unit(sun_lat, sun_lon)
    ux, uy, uz, vx, vy, vz = _basis_perpendicular_to(sx, sy, sz)
    ring = math.sqrt(max(0.0, 1.0 - mu * mu))
    points: list[tuple[float, float]] = []
    for index in range(sample_count):
        angle = 2.0 * math.pi * index / sample_count
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        px = mu * sx + ring * (cos_a * ux + sin_a * vx)
        py = mu * sy + ring * (cos_a * uy + sin_a * vy)
        pz = mu * sz + ring * (cos_a * uz + sin_a * vz)
        points.append(_unit_to_latlon(px, py, pz))
    return points


def sunglint_latlon(
    observation_time: struct_time,
    *,
    sub_satellite_lon_deg: float = _HIMAWARI_SUB_SATELLITE_LON_DEG,
) -> tuple[float, float]:
    """葵花视角下球面镜面耀斑点 ``(lat, lon)``（度）。

    对圆球近似：表面法向平分「指向太阳」与「指向卫星」的单位矢量，
    即 ``normalize(u_sun + u_sat)``。与直射点不同；耀斑亮心通常落在
    直射点与星下点 ``(0, 140.7°E)`` 之间。
    """
    sun_lat, sun_lon = subsolar_latlon(observation_time)
    ux, uy, uz = _latlon_to_unit(sun_lat, sun_lon)
    sx, sy, sz = _latlon_to_unit(0.0, sub_satellite_lon_deg)
    vx, vy, vz = ux + sx, uy + sy, uz + sz
    norm = math.sqrt(vx * vx + vy * vy + vz * vz)
    if norm <= 0.0:
        return sun_lat, sun_lon
    return _unit_to_latlon(vx / norm, vy / norm, vz / norm)
