"""程序目录旁 settings.json：读写与校验。"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.metadata.app_config import (
    DEFAULT_DOWNLOAD_INTERVAL_MINUTES,
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
    DEFAULT_RESOLUTION,
    DOWNLOAD_INTERVAL_MINUTES_CHOICES,
    IMAGE_RESOLUTION,
    PROGRAM_DIR_ABS_PATH,
)

SETTINGS_FILENAME = "settings.json"


def default_settings_path() -> Path:
    """返回程序目录下的 settings.json 路径。"""
    return PROGRAM_DIR_ABS_PATH / SETTINGS_FILENAME


def default_settings() -> dict[str, Any]:
    """内置默认配置。"""
    return {
        "resolution": DEFAULT_RESOLUTION,
        "auto_adjust": True,
        "margin_top_percent": DEFAULT_MARGIN_TOP_PERCENT,
        "margin_bottom_percent": DEFAULT_MARGIN_BOTTOM_PERCENT,
        "cleanup_after_apply": True,
        "use_yesterday_local_time": False,
        "reduce_banding": False,
        "show_typhoon_marker": False,
        "show_my_location": False,
        "download_interval_minutes": DEFAULT_DOWNLOAD_INTERVAL_MINUTES,
        "startup_enabled": False,
        "logging_enabled": False,
    }


def _coerce_resolution(value: Any) -> int | None:
    try:
        resolution = int(value)
    except (TypeError, ValueError):
        return None
    if resolution not in IMAGE_RESOLUTION:
        return None
    return resolution


def _coerce_percent(value: Any) -> float | None:
    try:
        percent = float(value)
    except (TypeError, ValueError):
        return None
    if not 0.0 <= percent <= 100.0:
        return None
    return percent


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _coerce_download_interval_minutes(value: Any) -> int | None:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None
    if minutes not in DOWNLOAD_INTERVAL_MINUTES_CHOICES:
        return None
    return minutes


def _coerce_last_run_key(value: Any) -> list[Any] | None:
    """校验指纹列表。

    完整 8 项：``[obs_time, grade, auto_adjust, top%, bottom%, reduce_banding,
    show_typhoon_marker, show_my_location]``。兼容旧版 5/6/7 项（缺省布尔为 ``False``）。
    """
    if not isinstance(value, (list, tuple)) or len(value) not in (5, 6, 7, 8):
        return None
    obs_time, grade, auto_adjust, top, bottom = value[:5]
    reduce_banding = value[5] if len(value) >= 6 else False
    show_typhoon_marker = value[6] if len(value) >= 7 else False
    show_my_location = value[7] if len(value) == 8 else False
    if not isinstance(obs_time, str) or not obs_time.strip():
        return None
    if not isinstance(grade, str) or not grade.strip():
        return None
    if not isinstance(auto_adjust, bool):
        return None
    if not isinstance(reduce_banding, bool):
        return None
    if not isinstance(show_typhoon_marker, bool):
        return None
    if not isinstance(show_my_location, bool):
        return None
    top_f = _coerce_percent(top)
    bottom_f = _coerce_percent(bottom)
    if top_f is None or bottom_f is None:
        return None
    return [
        obs_time.strip(),
        grade.strip(),
        auto_adjust,
        top_f,
        bottom_f,
        reduce_banding,
        show_typhoon_marker,
        show_my_location,
    ]


def _coerce_wallpaper_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _coerce_typhoon_center_cache(value: Any) -> dict[str, Any] | None:
    """校验 ``{observation_time, lat, lon}``。"""
    if not isinstance(value, dict):
        return None
    obs = value.get("observation_time")
    lat = value.get("lat")
    lon = value.get("lon")
    if not isinstance(obs, str) or not obs.strip():
        return None
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return {
        "observation_time": obs.strip(),
        "lat": float(lat),
        "lon": float(lon),
    }


def _coerce_my_location_cache(value: Any) -> dict[str, Any] | None:
    """校验 ``{lat, lon, fetched_at}``（Unix 秒）。"""
    if not isinstance(value, dict):
        return None
    lat = value.get("lat")
    lon = value.get("lon")
    fetched_at = value.get("fetched_at")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    if not isinstance(fetched_at, (int, float)):
        return None
    lat_f, lon_f = float(lat), float(lon)
    if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
        return None
    return {
        "lat": lat_f,
        "lon": lon_f,
        "fetched_at": float(fetched_at),
    }


# 字段表：增删 settings 键只改此处；sanitize 循环共用同一套 coerce。
_SETTINGS_FIELD_COERCERS: tuple[tuple[str, Callable[[Any], Any | None]], ...] = (
    ("resolution", _coerce_resolution),
    ("auto_adjust", _coerce_bool),
    ("margin_top_percent", _coerce_percent),
    ("margin_bottom_percent", _coerce_percent),
    ("cleanup_after_apply", _coerce_bool),
    ("use_yesterday_local_time", _coerce_bool),
    ("reduce_banding", _coerce_bool),
    ("show_typhoon_marker", _coerce_bool),
    ("show_my_location", _coerce_bool),
    ("download_interval_minutes", _coerce_download_interval_minutes),
    ("startup_enabled", _coerce_bool),
    ("logging_enabled", _coerce_bool),
    ("last_run_key", _coerce_last_run_key),
    ("last_wallpaper_path", _coerce_wallpaper_path),
    ("typhoon_center_cache", _coerce_typhoon_center_cache),
    ("my_location_cache", _coerce_my_location_cache),
)

_SETTINGS_KEYS = frozenset(key for key, _ in _SETTINGS_FIELD_COERCERS)


def sanitize_settings(raw: Any) -> dict[str, Any]:
    """校验并只保留合法字段；非法项跳过。"""
    if not isinstance(raw, dict):
        return {}

    cleaned: dict[str, Any] = {}
    for key, coerce in _SETTINGS_FIELD_COERCERS:
        if key not in raw:
            continue
        value = coerce(raw[key])
        if value is None:
            logging.warning("Ignoring invalid settings.%s: %r", key, raw[key])
        else:
            cleaned[key] = value

    unknown = set(raw) - _SETTINGS_KEYS
    if unknown:
        logging.info("Ignoring unknown settings keys: %s", sorted(unknown))

    return cleaned


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """从 JSON 加载配置；缺失或损坏时返回空 dict。"""
    settings_path = path if path is not None else default_settings_path()
    if not settings_path.is_file():
        logging.info("Settings file not found: %s", settings_path)
        return {}

    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        logging.exception("Failed to load settings from %s", settings_path)
        return {}

    cleaned = sanitize_settings(raw)
    logging.info("Loaded settings from %s", settings_path)
    logging.debug("Loaded settings payload: %s", cleaned)
    return cleaned


def save_settings(data: dict[str, Any], path: Path | None = None) -> bool:
    """原子写入 settings.json；成功返回 True。

    合并顺序：内置默认 → 已有文件 → 本次写入，避免部分更新冲掉其它键。
    """
    settings_path = path if path is not None else default_settings_path()
    existing = load_settings(settings_path) if settings_path.is_file() else {}
    payload = sanitize_settings({**default_settings(), **existing, **sanitize_settings(data)})

    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{SETTINGS_FILENAME}.",
            suffix=".tmp",
            dir=str(settings_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.write("\n")
            Path(tmp_name).replace(settings_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        logging.info("Saved settings to %s", settings_path)
        logging.debug("Saved settings payload: %s", payload)
        return True
    except OSError:
        logging.exception("Failed to save settings to %s", settings_path)
        return False


def settings_dict_from_job(
    *,
    resolution: int,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    cleanup_after_apply: bool,
    use_yesterday_local_time: bool = False,
    reduce_banding: bool = False,
    show_typhoon_marker: bool = False,
    show_my_location: bool = False,
    download_interval_minutes: int = DEFAULT_DOWNLOAD_INTERVAL_MINUTES,
) -> dict[str, Any]:
    """从壁纸任务字段组装可写入的 settings dict（不含 logging / 应用指纹）。"""
    return {
        "resolution": resolution,
        "auto_adjust": auto_adjust,
        "margin_top_percent": margin_top_percent,
        "margin_bottom_percent": margin_bottom_percent,
        "cleanup_after_apply": cleanup_after_apply,
        "use_yesterday_local_time": use_yesterday_local_time,
        "reduce_banding": reduce_banding,
        "show_typhoon_marker": show_typhoon_marker,
        "show_my_location": show_my_location,
        "download_interval_minutes": download_interval_minutes,
    }


def applied_run_state_from_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    """从 settings 字段还原内存中的 ``applied_run_state``。"""
    # 延迟导入：避免 settings ↔ wallpaper 顶层环依赖。
    from src.wallpaper.fingerprint import AppliedRunKey

    state: dict[str, Any] = {"last": None, "wallpaper_path": None}
    if not settings:
        return state
    run_key = AppliedRunKey.from_raw(settings.get("last_run_key"))
    if run_key is not None:
        state["last"] = run_key
    path = settings.get("last_wallpaper_path")
    if isinstance(path, str) and path.strip():
        state["wallpaper_path"] = path.strip()
    cache = settings.get("typhoon_center_cache")
    if isinstance(cache, dict):
        coerced = _coerce_typhoon_center_cache(cache)
        if coerced is not None:
            state["typhoon_center_cache"] = coerced
    my_loc = settings.get("my_location_cache")
    if isinstance(my_loc, dict):
        coerced_loc = _coerce_my_location_cache(my_loc)
        if coerced_loc is not None:
            state["my_location_cache"] = coerced_loc
    return state


def persist_applied_run_state(
    state: dict[str, Any],
    *,
    path: Path | None = None,
) -> bool:
    """将内存指纹与壁纸路径写回 settings.json。"""
    from src.wallpaper.fingerprint import AppliedRunKey

    payload: dict[str, Any] = {}
    last = AppliedRunKey.from_raw(state.get("last"))
    if last is not None:
        payload["last_run_key"] = list(last)
    wallpaper = state.get("wallpaper_path")
    if isinstance(wallpaper, str) and wallpaper.strip():
        payload["last_wallpaper_path"] = wallpaper.strip()
    cache = state.get("typhoon_center_cache")
    coerced = _coerce_typhoon_center_cache(cache) if cache is not None else None
    if coerced is not None:
        payload["typhoon_center_cache"] = coerced
    my_loc = state.get("my_location_cache")
    coerced_loc = _coerce_my_location_cache(my_loc) if my_loc is not None else None
    if coerced_loc is not None:
        payload["my_location_cache"] = coerced_loc
    if not payload:
        return False
    return save_settings(payload, path=path)


def resolve_runtime_settings(
    cli_values: dict[str, Any],
    *,
    file_settings: dict[str, Any] | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """合并：内置默认 → 文件 → CLI 中非 None 的显式值。"""
    merged = default_settings()
    loaded = file_settings if file_settings is not None else load_settings(path)
    merged.update(sanitize_settings(loaded))
    for key, value in cli_values.items():
        if value is not None and key in _SETTINGS_KEYS:
            merged[key] = value
    return sanitize_settings(merged) or default_settings()
