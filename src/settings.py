"""程序目录旁 settings.json：读写与校验。"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from src.metadata.soft_config import (
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
    logging.info("Loaded settings from %s: %s", settings_path, cleaned)
    return cleaned


def save_settings(data: dict[str, Any], path: Path | None = None) -> bool:
    """原子写入 settings.json；成功返回 True。"""
    settings_path = path if path is not None else default_settings_path()
    cleaned = sanitize_settings(data)
    if not cleaned:
        # 允许只写部分字段时仍落盘完整合法子集；空则仍写空对象无意义，合并默认再写
        cleaned = {}

    payload = {**default_settings(), **cleaned}
    # 再 sanitize 一次保证默认也被校验
    payload = sanitize_settings(payload)

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
        logging.info("Saved settings to %s: %s", settings_path, payload)
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
) -> dict[str, Any]:
    """从运行时字段组装可写入的 settings dict。"""
    return {
        "resolution": resolution,
        "auto_adjust": auto_adjust,
        "margin_top_percent": margin_top_percent,
        "margin_bottom_percent": margin_bottom_percent,
        "cleanup_after_apply": cleanup_after_apply,
    }


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
