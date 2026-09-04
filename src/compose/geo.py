"""葵花 8 号全圆盘经纬度 → 像素（对齐 NICT himawari8.fd）。"""

from __future__ import annotations

import math


# 与 jquery-k2go-tile-viewer.js ``geodeticSystem == "himawari8.fd"`` 一致。
_SUB_SATELLITE_LON_DEG = 140.7
_MARGIN_TOP = 0.006
_MARGIN_RIGHT = 0.0045
_MARGIN_BOTTOM = 0.006
_MARGIN_LEFT = 0.0045
_E2 = 0.00669438003
_THETA = 0.1535
_F = 6.613
_VRAD_DEG = 81.3025


def latlon_to_himawari_fd_xy(
    latitude: float,
    longitude: float,
    side: int,
) -> tuple[int, int] | None:
    """将大地经纬度投影到全圆盘正方形影像像素。

    Args:
        latitude: 纬度（度，北正）。
        longitude: 经度（度，东正）。
        side: 正方形影像边长（像素），如 ``N * 550``。

    Returns:
        ``(x, y)`` 像素坐标（左上原点）；点在可见盘外或 ``side`` 非法时 ``None``。
    """
    if side <= 0:
        return None

    lon_rad = ((longitude + 180.0 - _SUB_SATELLITE_LON_DEG) % 360.0 - 180.0) / 180.0 * math.pi
    lat_rad = ((latitude + 90.0) % 180.0 - 90.0) / 180.0 * math.pi
    radius = side * (1.0 - _MARGIN_RIGHT - _MARGIN_LEFT) / 2.0
    n = radius / math.sqrt(1.0 - _E2 * math.sin(lat_rad) * math.sin(lat_rad))
    vrad = _VRAD_DEG / 180.0 * math.pi

    # 超出葵花全盘视角则不可见；勿 clamp 到边缘，否则标注会贴在盘缘假阳性。
    if abs(lon_rad) > vrad or abs(lat_rad) > vrad:
        return None

    z = radius * _F - (n * math.cos(lat_rad) * math.cos(lon_rad))
    if z == 0:
        return None

    x = n * math.cos(lat_rad) * math.sin(lon_rad)
    y = (n * (1.0 - _E2)) * math.sin(lat_rad)
    x = side / 2.0 * math.atan(x / z) / _THETA
    y = side / 2.0 * math.atan(y / z) / _THETA
    x = x + side / 2.0
    y = side / 2.0 - y

    px = int(round(x))
    py = int(round(y))
    if not (0 <= px < side and 0 <= py < side):
        return None
    return px, py
