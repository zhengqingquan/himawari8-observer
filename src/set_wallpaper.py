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
        成功为 True；文件不存在为 False。
    """
    try:
        if wallpaper_path.exists() is False:
            raise FileNotFoundError

        logging.info(f"图片路径为：{wallpaper_path.resolve()}")

        # 必须使用绝对路径，否则可能落到默认纯色背景。
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 1
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, os.path.abspath(wallpaper_path), SPIF_UPDATEINIFILE
        )

        logging.info("图片替换完成。")

        return True
    except FileNotFoundError:
        logging.warning(f"图片不存在：{wallpaper_path}")
        return False
