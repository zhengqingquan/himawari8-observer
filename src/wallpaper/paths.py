"""成图中间路径命名、桌面占用绕写与 base/disk 落盘辅助。"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, MutableMapping

from src.wallpaper.desktop import wallpaper_paths_match

AppliedRunState = MutableMapping[str, Any]


def wallpaper_base_path(wallpaper_path: Path) -> Path:
    """未去色带、无台风/定位标记的底图路径：``{stem}_base{suffix}``。"""
    return wallpaper_path.with_name(f"{wallpaper_path.stem}_base{wallpaper_path.suffix}")


def wallpaper_disk_path(equal_or_wallpaper: Path) -> Path:
    """等分圆盘（未修边）路径：由等分图或 ``*_adjust`` 成品推导 ``{stem}_disk``。"""
    stem = equal_or_wallpaper.stem
    if stem.endswith("_adjust"):
        stem = stem[: -len("_adjust")]
    elif stem.endswith("_disk"):
        return equal_or_wallpaper
    return equal_or_wallpaper.with_name(f"{stem}_disk{equal_or_wallpaper.suffix}")


def equal_path_from_disk(disk_path: Path) -> Path:
    """由 ``*_disk`` 还原等分图路径。"""
    stem = disk_path.stem
    if stem.endswith("_disk"):
        stem = stem[: -len("_disk")]
    return disk_path.with_name(f"{stem}{disk_path.suffix}")


def alternate_wallpaper_path(path: Path) -> Path:
    """在 ``name`` 与 ``name_b`` 之间切换，避免覆盖正被桌面占用的文件。"""
    stem = path.stem
    if stem.endswith("_b"):
        return path.with_name(f"{stem[:-2]}{path.suffix}")
    return path.with_name(f"{stem}_b{path.suffix}")


def pick_writable_wallpaper_path(
    preferred: Path,
    *,
    current_desktop: str | Path | None = None,
) -> Path:
    """若 ``preferred`` 正是当前桌面壁纸，改写到交替路径。"""
    if current_desktop and wallpaper_paths_match(current_desktop, preferred):
        alt = alternate_wallpaper_path(preferred)
        logging.info(
            "Desktop wallpaper locks %s; writing to %s instead",
            preferred,
            alt,
        )
        return alt
    return preferred


def copy2_wallpaper(src: Path, dest: Path) -> Path:
    """``shutil.copy2``；遇 WinError 1224（桌面映射占用）则写入交替路径。"""
    try:
        shutil.copy2(src, dest)
        return dest
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1224:
            raise
        alt = alternate_wallpaper_path(dest)
        logging.info("copy2 hit WinError 1224 on %s; writing to %s", dest, alt)
        shutil.copy2(src, alt)
        return alt


def wallpaper_output_path(equal_path: Path, *, auto_adjust: bool) -> Path:
    """按是否修边决定成品路径（修边为 ``*_adjust``）。"""
    if auto_adjust:
        return equal_path.with_name(f"{equal_path.stem}_adjust{equal_path.suffix}")
    return equal_path


def path_str(path: Path) -> str:
    """优先 ``resolve()`` 的绝对路径字符串；失败则退回 ``str(path)``。"""
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def ensure_unmarked_base(wallpaper_path: Path) -> Path:
    """若 ``*_base`` 缺失，把当前成品复制为底图（已存在则不覆盖）。"""
    base = wallpaper_base_path(wallpaper_path)
    if base.is_file():
        return base
    if not wallpaper_path.is_file():
        return base
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper_path, base)
    return base


def save_unmarked_base(wallpaper_path: Path) -> Path:
    """将当前成品（须为未去色带、无台风标记）写入 ``*_base``（覆盖）。"""
    base = wallpaper_base_path(wallpaper_path)
    if not wallpaper_path.is_file():
        return base
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper_path, base)
    return base


def save_disk_copy(equal_path: Path) -> Path:
    """将等分圆盘复制为 ``*_disk``（覆盖），供修边后处理复用。"""
    disk = wallpaper_disk_path(equal_path)
    if not equal_path.is_file():
        return disk
    disk.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(equal_path, disk)
    return disk


def _resolve_state_path(
    applied_run_state: AppliedRunState | None,
    key: str,
    wallpaper_path: Path,
    fallback: Callable[[Path], Path],
) -> Path:
    """若 state 中 ``key`` 指向现存文件则用之，否则 ``fallback(wallpaper_path)``。"""
    if applied_run_state is not None:
        raw = applied_run_state.get(key)
        if isinstance(raw, str) and raw.strip():
            candidate = Path(raw.strip())
            if candidate.is_file():
                return candidate
    return fallback(wallpaper_path)


def resolve_base_path(
    applied_run_state: AppliedRunState | None,
    wallpaper_path: Path,
) -> Path:
    return _resolve_state_path(
        applied_run_state,
        "wallpaper_base_path",
        wallpaper_path,
        wallpaper_base_path,
    )


def resolve_disk_path(
    applied_run_state: AppliedRunState | None,
    wallpaper_path: Path,
) -> Path:
    return _resolve_state_path(
        applied_run_state,
        "wallpaper_disk_path",
        wallpaper_path,
        wallpaper_disk_path,
    )
