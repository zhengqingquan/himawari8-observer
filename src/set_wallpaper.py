"""通过 Win32 API 设置桌面壁纸。"""

from __future__ import annotations

import ctypes
import logging
import os
from pathlib import Path


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
