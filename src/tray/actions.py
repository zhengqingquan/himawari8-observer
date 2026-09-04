"""托盘菜单动作：关于、退出、日志、开机启动、检查更新等。"""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from datetime import datetime, timezone, tzinfo
from pathlib import Path

import webbrowser
from PIL import Image

from src.event import request_shutdown
from src.log import is_logging_enabled, set_logging_enabled
from src.metadata.app_config import LOG_PATH, PROGRAM_DIR_ABS_PATH
from src.metadata.app_info import (
    DESCRIPTION,
    PROGRAM_NAME,
    RELEASES_URL,
    SOFTWARE_VERSION,
    WEBSITE,
)
from src.settings import save_settings, settings_dict_from_job
from src.startup import apply_startup_enabled, is_startup_set
from src.version_check import UpdateStatus, check_for_update
from src.wallpaper.job import WallpaperJobRef

_TRAY_ICON_NAME = "tray_icon.png"
_OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"

# Win32 MessageBox：类型 / 图标 / 置顶与前台。
_MB_OK = 0x00000000
_MB_YESNO = 0x00000004
_MB_ICONWARNING = 0x00000030
_MB_ICONQUESTION = 0x00000020
_MB_ICONINFORMATION = 0x00000040
_MB_TOPMOST = 0x00040000
_MB_SETFOREGROUND = 0x00010000
_MB_TOPMOST_FOREGROUND = _MB_TOPMOST | _MB_SETFOREGROUND
_MB_OK_INFO = _MB_OK | _MB_ICONINFORMATION | _MB_TOPMOST_FOREGROUND
_MB_OK_WARN = _MB_OK | _MB_ICONWARNING | _MB_TOPMOST_FOREGROUND
_MB_YESNO_QUESTION = _MB_YESNO | _MB_ICONQUESTION | _MB_TOPMOST_FOREGROUND
_IDYES = 6


def format_observation_local_time(
    utc_time_str: str,
    *,
    local_tz: tzinfo | None = None,
) -> str:
    """将 NICT UTC 观测时间字符串换算为本机（或指定）时区时间。

    Args:
        utc_time_str: ``YYYY-MM-DD HH:MM:SS``（按 UTC 解释）。
        local_tz: 目标时区；默认使用系统本地时区。

    Returns:
        换算后的 ``YYYY-MM-DD HH:MM:SS``。
    """
    utc_dt = datetime.strptime(utc_time_str, _OBS_TIME_FMT).replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime(_OBS_TIME_FMT)


def format_tray_icon_title(
    obs_time: str | None,
    *,
    pixel_side: int | None = None,
    local_tz: tzinfo | None = None,
) -> str:
    """托盘悬停标题：有观测时间时附带本地/UTC 与上墙分辨率，否则仅程序名。"""
    if not obs_time:
        return PROGRAM_NAME
    try:
        local = format_observation_local_time(obs_time, local_tz=local_tz)
    except (ValueError, OSError):
        logging.exception("Failed to format tray icon title for observation time: %s", obs_time)
        return PROGRAM_NAME
    lines = [
        PROGRAM_NAME,
        f"壁纸时间（本地）：{local}",
        f"壁纸时间（UTC）：{obs_time}",
    ]
    if pixel_side is not None:
        lines.append(f"分辨率：{pixel_side}")
    return "\n".join(lines)


def _tray_icon_path() -> Path:
    """解析托盘图标路径。

    Returns:
        打包环境优先 ``_MEIPASS/assets``；开发时为仓库根 ``assets/``。
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "assets" / _TRAY_ICON_NAME
            if bundled.is_file():
                return bundled
    return Path(__file__).resolve().parents[2] / "assets" / _TRAY_ICON_NAME


def create_image():
    """加载托盘图标图像。"""
    icon_path = _tray_icon_path()
    try:
        return Image.open(icon_path)
    except OSError:
        logging.exception("Failed to load tray icon: %s", icon_path)
        raise


def on_clicked(icon, item):
    """弹出关于对话框（独立线程，避免卡住 pystray 消息循环）。"""
    message_text = f"""\
软件：{PROGRAM_NAME}
版本：{SOFTWARE_VERSION}
介绍：{DESCRIPTION}
"""

    def show_about():
        ctypes.windll.user32.MessageBoxW(
            None,
            message_text,
            f"关于 {PROGRAM_NAME}",
            _MB_OK_INFO,
        )

    threading.Thread(target=show_about, daemon=True).start()


def on_quit(icon, item):
    """退出托盘并结束主线程保活。"""
    icon.stop()
    request_shutdown()


def on_open_github(icon, item):
    """在浏览器中打开 GitHub 仓库。"""
    webbrowser.open_new(WEBSITE)


def on_check_update(icon, item):
    """检查 GitHub 是否有新版本（独立线程，避免卡住托盘）。"""

    def run_check():
        result = check_for_update()
        if result.status is UpdateStatus.FAILED:
            ctypes.windll.user32.MessageBoxW(
                None,
                "检查更新失败，请稍后重试或手动打开 GitHub Releases。",
                "检查更新",
                _MB_OK_WARN,
            )
            return
        if result.status is UpdateStatus.UP_TO_DATE:
            ctypes.windll.user32.MessageBoxW(
                None,
                f"当前已是最新版本（{result.current_version}）。",
                "检查更新",
                _MB_OK_INFO,
            )
            return
        latest = result.latest_version or ""
        answer = ctypes.windll.user32.MessageBoxW(
            None,
            f"发现新版本 {latest}（当前 {result.current_version}）。是否打开 Releases 下载？",
            "检查更新",
            _MB_YESNO_QUESTION,
        )
        if answer == _IDYES:
            webbrowser.open_new(RELEASES_URL)

    threading.Thread(target=run_check, daemon=True).start()


def on_open_program_dir(icon, item):
    """用资源管理器打开程序所在目录。"""
    program_dir = PROGRAM_DIR_ABS_PATH
    program_dir.mkdir(parents=True, exist_ok=True)
    os.startfile(program_dir)


def on_startup(icon, item):
    """切换开机启动，并写入 settings.json（默认关闭）。"""
    enabled = not is_startup_set()
    apply_startup_enabled(enabled)
    save_settings({"startup_enabled": enabled})
    logging.info("Startup on boot %s", "enabled" if enabled else "disabled")


def on_open_log(icon, item):
    """用系统默认方式打开日志文件。"""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.touch(exist_ok=True)
    os.startfile(LOG_PATH)


def on_toggle_logging(icon, item):
    """切换日志开关并写入 settings.json。"""
    enabled = not is_logging_enabled()
    set_logging_enabled(enabled)
    save_settings({"logging_enabled": enabled})
    logging.info("Logging %s", "enabled" if enabled else "disabled")


def persist_job_settings(job_ref: WallpaperJobRef) -> None:
    """将当前托盘可改项写入程序旁 settings.json。"""
    save_settings(
        settings_dict_from_job(
            resolution=job_ref.pixel_side,
            auto_adjust=job_ref.auto_adjust,
            margin_top_percent=job_ref.margin_top_percent,
            margin_bottom_percent=job_ref.margin_bottom_percent,
            cleanup_after_apply=job_ref.cleanup_after_apply,
            use_yesterday_local_time=job_ref.use_yesterday_local_time,
            reduce_banding=job_ref.reduce_banding,
            show_typhoon_marker=job_ref.show_typhoon_marker,
            show_my_location=job_ref.show_my_location,
            show_subsolar_point=job_ref.show_subsolar_point,
            download_interval_minutes=job_ref.download_interval_minutes,
        )
    )
