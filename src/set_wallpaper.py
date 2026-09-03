"""通过 Win32 API 设置 / 读取桌面壁纸。"""

from __future__ import annotations

import ctypes
import logging
import os
from pathlib import Path

_SPI_GETDESKWALLPAPER = 0x0073
_WALLPAPER_PATH_BUF_CHARS = 1024


def get_desktop_wallpaper() -> str | None:
    """读取当前桌面壁纸路径；失败或未设置时返回 ``None``。"""
    try:
        buf = ctypes.create_unicode_buffer(_WALLPAPER_PATH_BUF_CHARS)
        ok = ctypes.windll.user32.SystemParametersInfoW(
            _SPI_GETDESKWALLPAPER,
            _WALLPAPER_PATH_BUF_CHARS,
            buf,
            0,
        )
        if not ok:
            logging.warning("SystemParametersInfoW failed to get desktop wallpaper path")
            return None
        path = buf.value.strip()
        return path or None
    except OSError:
        logging.exception("Failed to get desktop wallpaper path")
        return None


def wallpaper_paths_match(left: str | Path | None, right: str | Path | None) -> bool:
    """比较两条壁纸路径是否指向同一文件（规范化后）。"""
    if not left or not right:
        return False
    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return os.path.normcase(os.path.abspath(str(left))) == os.path.normcase(
            os.path.abspath(str(right))
        )


def set_wallpaper(wallpaper_path: Path) -> bool:
    """按路径替换桌面背景（Win7 可能不支持 PNG）。

    Args:
        wallpaper_path: 壁纸图片路径（须存在；内部会转为绝对路径）。

    Returns:
        成功为 True；失败为 False。
    """
    try:
        if not wallpaper_path.exists():
            logging.warning("Wallpaper file not found: %s", wallpaper_path)
            return False

        abs_path = os.path.abspath(wallpaper_path)
        logging.info("Setting desktop wallpaper: %s", abs_path)

        # Absolute path is required; otherwise Windows may fall back to a solid color.
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 1
        ok = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE
        )
        if not ok:
            logging.error("SystemParametersInfoW failed for wallpaper: %s", abs_path)
            return False

        logging.info("Desktop wallpaper updated")
        return True
    except OSError:
        logging.exception("Failed to set desktop wallpaper: %s", wallpaper_path)
        return False
