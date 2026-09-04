"""壁纸叠加标注：台风中心与「我的位置」（含 state 缓存）。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from time import strftime, struct_time

from PIL import Image

from src.compose.equal import compute_margin_layout, get_primary_screen_size
from src.compose.geo import latlon_to_himawari_fd_xy
from src.compose.overlay import draw_typhoon_marker
from src.wallpaper.fingerprint import OBS_TIME_FMT
from src.wallpaper.paths import AppliedRunState

FetchTyphoonCenter = Callable[[struct_time], tuple[float, float] | None]
FetchIpLatlon = Callable[[], tuple[float, float] | None]

_MY_LOCATION_CACHE_TTL_SEC = 24 * 60 * 60
_MY_LOCATION_MARKER_COLOR = (64, 156, 255)
_MY_LOCATION_MARKER_LABEL = "ME"


def store_typhoon_center_cache(
    applied_run_state: AppliedRunState | None,
    observation_time: str,
    lat: float,
    lon: float,
) -> None:
    if applied_run_state is None:
        return
    applied_run_state["typhoon_center_cache"] = {
        "observation_time": observation_time,
        "lat": float(lat),
        "lon": float(lon),
    }


def cached_typhoon_center(
    applied_run_state: AppliedRunState | None,
    observation_time: str,
) -> tuple[float, float] | None:
    """仅当缓存观测时间与当前一致时返回 ``(lat, lon)``。"""
    if applied_run_state is None:
        return None
    raw = applied_run_state.get("typhoon_center_cache")
    if not isinstance(raw, dict):
        return None
    obs = raw.get("observation_time")
    lat = raw.get("lat")
    lon = raw.get("lon")
    if obs != observation_time:
        return None
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return float(lat), float(lon)


def draw_typhoon_marker_at(
    *,
    wallpaper_path: Path,
    pic_side: int,
    lat: float,
    lon: float,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    label: str = "TY",
    color: tuple[int, int, int] = (241, 166, 39),
) -> bool:
    """按经纬度在壁纸上画标记；成功返回 True。"""
    xy = latlon_to_himawari_fd_xy(lat, lon, pic_side)
    if xy is None:
        logging.info("Marker projects outside full-disk frame; skipping")
        return False
    draw_xy = xy
    if auto_adjust:
        try:
            with Image.open(wallpaper_path) as img:
                canvas_w, canvas_h = img.size
        except OSError:
            logging.exception("Failed to open wallpaper for marker offset: %s", wallpaper_path)
            return False
        if canvas_w != pic_side or canvas_h != pic_side:
            screen_width, screen_height = get_primary_screen_size()
            _, _, image_x, image_y = compute_margin_layout(
                pic_side,
                screen_width,
                screen_height,
                top_percent=margin_top_percent,
                bottom_percent=margin_bottom_percent,
            )
            draw_xy = (image_x + xy[0], image_y + xy[1])
    return draw_typhoon_marker(wallpaper_path, draw_xy, label=label, color=color)


def apply_typhoon_marker_if_needed(
    *,
    wallpaper_path: Path,
    pic_side: int,
    observation_time: struct_time,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    fetch_typhoon_center_fn: FetchTyphoonCenter,
    applied_run_state: AppliedRunState | None = None,
) -> None:
    """拉取台风中心、写入对应该观测时间的缓存并标注；失败只记日志。"""
    center = fetch_typhoon_center_fn(observation_time)
    if center is None:
        return
    lat, lon = center
    obs_str = strftime(OBS_TIME_FMT, observation_time)
    store_typhoon_center_cache(applied_run_state, obs_str, lat, lon)
    draw_typhoon_marker_at(
        wallpaper_path=wallpaper_path,
        pic_side=pic_side,
        lat=lat,
        lon=lon,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
    )


def store_my_location_cache(
    applied_run_state: AppliedRunState | None,
    lat: float,
    lon: float,
    *,
    fetched_at: float | None = None,
) -> None:
    if applied_run_state is None:
        return
    applied_run_state["my_location_cache"] = {
        "lat": float(lat),
        "lon": float(lon),
        "fetched_at": float(time.time() if fetched_at is None else fetched_at),
    }


def cached_my_location(
    applied_run_state: AppliedRunState | None,
    *,
    now: float | None = None,
    ttl_sec: float = _MY_LOCATION_CACHE_TTL_SEC,
) -> tuple[float, float] | None:
    """缓存未过期时返回 ``(lat, lon)``。"""
    if applied_run_state is None:
        return None
    raw = applied_run_state.get("my_location_cache")
    if not isinstance(raw, dict):
        return None
    lat = raw.get("lat")
    lon = raw.get("lon")
    fetched_at = raw.get("fetched_at")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    if not isinstance(fetched_at, (int, float)):
        return None
    clock = time.time() if now is None else now
    if clock - float(fetched_at) > ttl_sec:
        return None
    return float(lat), float(lon)


def apply_my_location_marker_if_needed(
    *,
    wallpaper_path: Path,
    pic_side: int,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    fetch_ip_latlon_fn: FetchIpLatlon,
    applied_run_state: AppliedRunState | None = None,
    allow_network: bool = True,
) -> None:
    """用缓存或 IP 粗定位在壁纸上画「我」标记；失败只记日志。

    Args:
        allow_network: 为 False 时仅使用未过期缓存；为 True 时缓存缺失/过期可联网。
    """
    center = cached_my_location(applied_run_state)
    if center is None and allow_network:
        center = fetch_ip_latlon_fn()
        if center is not None:
            store_my_location_cache(applied_run_state, center[0], center[1])
    if center is None:
        if not allow_network:
            logging.info("Postprocess fast path: no my-location cache; marker not drawn")
        return
    lat, lon = center
    draw_typhoon_marker_at(
        wallpaper_path=wallpaper_path,
        pic_side=pic_side,
        lat=lat,
        lon=lon,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
        label=_MY_LOCATION_MARKER_LABEL,
        color=_MY_LOCATION_MARKER_COLOR,
    )
