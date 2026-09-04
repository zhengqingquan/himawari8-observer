"""后处理门面：成图指纹 / 路径 / 标注 / 快路径（兼容既有 import）。"""

from __future__ import annotations

from src.compose.overlay import draw_typhoon_marker
from src.wallpaper.fast_path import (
    GetDesktopWallpaper,
    SetWallpaper,
    try_postprocess_fast_path,
)
from src.wallpaper.fingerprint import (
    AppliedRunKey,
    OBS_TIME_FMT,
    build_applied_run_key,
    layout_or_postprocess_differs,
    obs_grade_match,
    provisional_run_key_from_last,
    remember_applied,
)
from src.wallpaper.markers import (
    FetchIpLatlon,
    FetchTyphoonCenter,
    apply_my_location_marker_if_needed,
    apply_typhoon_marker_if_needed,
    cached_my_location,
    cached_typhoon_center,
    draw_typhoon_marker_at,
    store_my_location_cache,
    store_typhoon_center_cache,
)
from src.wallpaper.paths import (
    AppliedRunState,
    alternate_wallpaper_path,
    copy2_wallpaper,
    ensure_unmarked_base,
    equal_path_from_disk,
    path_str,
    pick_writable_wallpaper_path,
    resolve_base_path,
    resolve_disk_path,
    save_disk_copy,
    save_unmarked_base,
    wallpaper_base_path,
    wallpaper_disk_path,
    wallpaper_output_path,
)

__all__ = [
    "AppliedRunKey",
    "AppliedRunState",
    "FetchIpLatlon",
    "FetchTyphoonCenter",
    "GetDesktopWallpaper",
    "OBS_TIME_FMT",
    "SetWallpaper",
    "alternate_wallpaper_path",
    "apply_my_location_marker_if_needed",
    "apply_typhoon_marker_if_needed",
    "build_applied_run_key",
    "cached_my_location",
    "cached_typhoon_center",
    "copy2_wallpaper",
    "draw_typhoon_marker",
    "draw_typhoon_marker_at",
    "ensure_unmarked_base",
    "equal_path_from_disk",
    "layout_or_postprocess_differs",
    "obs_grade_match",
    "path_str",
    "pick_writable_wallpaper_path",
    "provisional_run_key_from_last",
    "remember_applied",
    "resolve_base_path",
    "resolve_disk_path",
    "save_disk_copy",
    "save_unmarked_base",
    "store_my_location_cache",
    "store_typhoon_center_cache",
    "try_postprocess_fast_path",
    "wallpaper_base_path",
    "wallpaper_disk_path",
    "wallpaper_output_path",
]
