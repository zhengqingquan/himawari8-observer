"""程序目录旁 settings.json：读写与校验。"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from src.metadata.app_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
    DEFAULT_RESOLUTION,
    IMAGE_RESOLUTION,
    PROGRAM_DIR_ABS_PATH,
)

SETTINGS_FILENAME = "settings.json"

_SETTINGS_KEYS = frozenset(
    {
        "resolution",
        "auto_adjust",
        "margin_top_percent",
        "margin_bottom_percent",
        "cleanup_after_apply",
        "use_yesterday_local_time",
        "reduce_banding",
        "show_typhoon_marker",
        "startup_enabled",
        "logging_enabled",
        "last_run_key",
        "last_wallpaper_path",
        "typhoon_center_cache",
    }
)


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


def _coerce_last_run_key(value: Any) -> list[Any] | None:
    """校验指纹列表。

    完整 7 项：``[obs_time, grade, auto_adjust, top%, bottom%, reduce_banding,
    show_typhoon_marker]``。兼容旧版 5/6 项（缺省布尔为 ``False``）。
    """
    if not isinstance(value, (list, tuple)) or len(value) not in (5, 6, 7):
        return None
    obs_time, grade, auto_adjust, top, bottom = value[:5]
    reduce_banding = value[5] if len(value) >= 6 else False
    show_typhoon_marker = value[6] if len(value) == 7 else False
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


def sanitize_settings(raw: Any) -> dict[str, Any]:
    """校验并只保留合法字段；非法项跳过。"""
    if not isinstance(raw, dict):
        return {}

    cleaned: dict[str, Any] = {}

    if "resolution" in raw:
        resolution = _coerce_resolution(raw["resolution"])
        if resolution is None:
            logging.warning("Ignoring invalid settings.resolution: %r", raw["resolution"])
        else:
            cleaned["resolution"] = resolution

    if "auto_adjust" in raw:
        auto_adjust = _coerce_bool(raw["auto_adjust"])
        if auto_adjust is None:
            logging.warning("Ignoring invalid settings.auto_adjust: %r", raw["auto_adjust"])
        else:
            cleaned["auto_adjust"] = auto_adjust

    if "margin_top_percent" in raw:
        top = _coerce_percent(raw["margin_top_percent"])
        if top is None:
            logging.warning(
                "Ignoring invalid settings.margin_top_percent: %r",
                raw["margin_top_percent"],
            )
        else:
            cleaned["margin_top_percent"] = top

    if "margin_bottom_percent" in raw:
        bottom = _coerce_percent(raw["margin_bottom_percent"])
        if bottom is None:
            logging.warning(
                "Ignoring invalid settings.margin_bottom_percent: %r",
                raw["margin_bottom_percent"],
            )
        else:
            cleaned["margin_bottom_percent"] = bottom

    if "cleanup_after_apply" in raw:
        cleanup = _coerce_bool(raw["cleanup_after_apply"])
        if cleanup is None:
            logging.warning(
                "Ignoring invalid settings.cleanup_after_apply: %r",
                raw["cleanup_after_apply"],
            )
        else:
            cleaned["cleanup_after_apply"] = cleanup

    if "use_yesterday_local_time" in raw:
        yesterday = _coerce_bool(raw["use_yesterday_local_time"])
        if yesterday is None:
            logging.warning(
                "Ignoring invalid settings.use_yesterday_local_time: %r",
                raw["use_yesterday_local_time"],
            )
        else:
            cleaned["use_yesterday_local_time"] = yesterday

    if "reduce_banding" in raw:
        reduce_banding = _coerce_bool(raw["reduce_banding"])
        if reduce_banding is None:
            logging.warning(
                "Ignoring invalid settings.reduce_banding: %r",
                raw["reduce_banding"],
            )
        else:
            cleaned["reduce_banding"] = reduce_banding

    if "show_typhoon_marker" in raw:
        show_typhoon_marker = _coerce_bool(raw["show_typhoon_marker"])
        if show_typhoon_marker is None:
            logging.warning(
                "Ignoring invalid settings.show_typhoon_marker: %r",
                raw["show_typhoon_marker"],
            )
        else:
            cleaned["show_typhoon_marker"] = show_typhoon_marker

    if "startup_enabled" in raw:
        startup_enabled = _coerce_bool(raw["startup_enabled"])
        if startup_enabled is None:
            logging.warning(
                "Ignoring invalid settings.startup_enabled: %r",
                raw["startup_enabled"],
            )
        else:
            cleaned["startup_enabled"] = startup_enabled

    if "logging_enabled" in raw:
        logging_enabled = _coerce_bool(raw["logging_enabled"])
        if logging_enabled is None:
            logging.warning(
                "Ignoring invalid settings.logging_enabled: %r",
                raw["logging_enabled"],
            )
        else:
            cleaned["logging_enabled"] = logging_enabled

    if "last_run_key" in raw:
        run_key = _coerce_last_run_key(raw["last_run_key"])
        if run_key is None:
            logging.warning("Ignoring invalid settings.last_run_key: %r", raw["last_run_key"])
        else:
            cleaned["last_run_key"] = run_key

    if "last_wallpaper_path" in raw:
        wallpaper_path = _coerce_wallpaper_path(raw["last_wallpaper_path"])
        if wallpaper_path is None:
            logging.warning(
                "Ignoring invalid settings.last_wallpaper_path: %r",
                raw["last_wallpaper_path"],
            )
        else:
            cleaned["last_wallpaper_path"] = wallpaper_path

    if "typhoon_center_cache" in raw:
        cache = _coerce_typhoon_center_cache(raw["typhoon_center_cache"])
        if cache is None:
            logging.warning(
                "Ignoring invalid settings.typhoon_center_cache: %r",
                raw["typhoon_center_cache"],
            )
        else:
            cleaned["typhoon_center_cache"] = cache

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
    }


def applied_run_state_from_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    """从 settings 字段还原内存中的 ``applied_run_state``。"""
    state: dict[str, Any] = {"last": None, "wallpaper_path": None}
    if not settings:
        return state
    run_key = settings.get("last_run_key")
    if isinstance(run_key, list) and len(run_key) == 7:
        state["last"] = (
            str(run_key[0]),
            str(run_key[1]),
            bool(run_key[2]),
            float(run_key[3]),
            float(run_key[4]),
            bool(run_key[5]),
            bool(run_key[6]),
        )
    path = settings.get("last_wallpaper_path")
    if isinstance(path, str) and path.strip():
        state["wallpaper_path"] = path.strip()
    cache = settings.get("typhoon_center_cache")
    if isinstance(cache, dict):
        coerced = _coerce_typhoon_center_cache(cache)
        if coerced is not None:
            state["typhoon_center_cache"] = coerced
    return state


def persist_applied_run_state(
    state: dict[str, Any],
    *,
    path: Path | None = None,
) -> bool:
    """将内存指纹与壁纸路径写回 settings.json。"""
    payload: dict[str, Any] = {}
    last = state.get("last")
    if isinstance(last, tuple) and len(last) == 7:
        payload["last_run_key"] = [
            str(last[0]),
            str(last[1]),
            bool(last[2]),
            float(last[3]),
            float(last[4]),
            bool(last[5]),
            bool(last[6]),
        ]
    wallpaper = state.get("wallpaper_path")
    if isinstance(wallpaper, str) and wallpaper.strip():
        payload["last_wallpaper_path"] = wallpaper.strip()
    cache = state.get("typhoon_center_cache")
    coerced = _coerce_typhoon_center_cache(cache) if cache is not None else None
    if coerced is not None:
        payload["typhoon_center_cache"] = coerced
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
