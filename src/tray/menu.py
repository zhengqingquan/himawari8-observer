"""系统托盘菜单：壁纸时间、分辨率、修边、暂停、开机启动、日志与关于。"""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from datetime import datetime, timezone, tzinfo
from pathlib import Path

import pystray
import webbrowser
from PIL import Image

from src.event.event import request_shutdown
from src.log.log import is_logging_enabled, set_logging_enabled
from src.metadata.soft_config import (
    IMAGE_RESOLUTION,
    LOG_PATH,
    MARGIN_PERCENT_CHOICES,
    PROGRAM_DIR_ABS_PATH,
)
from src.metadata.soft_info import (
    DESCRIPTION,
    PROGRAM_NAME,
    RELEASES_URL,
    SOFTWARE_VERSION,
    WEBSITE,
)
from src.settings import save_settings, settings_dict_from_job
from src.startup import add_to_startup_exe, is_startup_set, remove_from_startup_exe
from src.update_check import UpdateStatus, check_for_update
from src.wallpaper.job import WallpaperJobRef
from src.wallpaper.update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)

_TRAY_ICON_NAME = "tray_icon.png"
_OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"


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
        # MB_OK | MB_ICONINFORMATION | MB_TOPMOST | MB_SETFOREGROUND
        ctypes.windll.user32.MessageBoxW(
            None,
            message_text,
            f"关于 {PROGRAM_NAME}",
            0x00050040,
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
                0x00050030,  # MB_OK | MB_ICONWARNING | MB_TOPMOST | MB_SETFOREGROUND
            )
            return
        if result.status is UpdateStatus.UP_TO_DATE:
            ctypes.windll.user32.MessageBoxW(
                None,
                f"当前已是最新版本（{result.current_version}）。",
                "检查更新",
                0x00050040,  # MB_OK | MB_ICONINFORMATION | ...
            )
            return
        latest = result.latest_version or ""
        answer = ctypes.windll.user32.MessageBoxW(
            None,
            f"发现新版本 {latest}（当前 {result.current_version}）。是否打开 Releases 下载？",
            "检查更新",
            0x00050024,  # MB_YESNO | MB_ICONQUESTION | MB_TOPMOST | MB_SETFOREGROUND
        )
        if answer == 6:  # IDYES
            webbrowser.open_new(RELEASES_URL)

    threading.Thread(target=run_check, daemon=True).start()


def on_open_program_dir(icon, item):
    """用资源管理器打开程序所在目录。"""
    program_dir = PROGRAM_DIR_ABS_PATH
    program_dir.mkdir(parents=True, exist_ok=True)
    os.startfile(program_dir)


def on_startup(icon, item):
    """切换开机启动注册表项。"""
    if is_startup_set():
        remove_from_startup_exe()
    else:
        add_to_startup_exe()


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


def _persist_job_settings(job_ref: WallpaperJobRef) -> None:
    """将当前托盘可改项写入程序旁 settings.json。"""
    save_settings(
        settings_dict_from_job(
            resolution=job_ref.pixel_side,
            auto_adjust=job_ref.auto_adjust,
            margin_top_percent=job_ref.margin_top_percent,
            margin_bottom_percent=job_ref.margin_bottom_percent,
            cleanup_after_apply=job_ref.cleanup_after_apply,
        )
    )


def setup_tray_icon(job_ref: WallpaperJobRef):
    """创建并阻塞运行系统托盘图标。

    Args:
        job_ref: 托盘与定时器共享的壁纸任务引用，由 ``src.app`` 注入。
    """

    def on_update_wallpaper(icon, item):
        threading.Thread(
            target=lambda: run_wallpaper_update(
                pipeline=job_ref,
                respect_pause=False,
                progressive=True,
            ),
            daemon=True,
        ).start()

    def on_toggle_pause(icon, item):
        if is_paused():
            resume()
        else:
            pause()

    def make_resolution_item(pixel_side: int):
        def on_select(icon, item):
            job_ref.set_pixel_side(pixel_side)
            _persist_job_settings(job_ref)
            logging.info(
                "Resolution set to %spx (grade %s)",
                pixel_side,
                job_ref.resolution_grade,
            )
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"分辨率 {pixel_side}",
            on_select,
            checked=lambda item: job_ref.pixel_side == pixel_side,
            radio=True,
        )

    def on_toggle_adjust(icon, item):
        enabled = not job_ref.auto_adjust
        job_ref.set_auto_adjust(enabled)
        _persist_job_settings(job_ref)
        logging.info("Margin adjust %s", "enabled" if enabled else "disabled")
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def on_toggle_cleanup(icon, item):
        enabled = not job_ref.cleanup_after_apply
        job_ref.set_cleanup_after_apply(enabled)
        _persist_job_settings(job_ref)
        logging.info("Cleanup after apply %s", "enabled" if enabled else "disabled")

    def make_margin_top_item(percent: float):
        def on_select(icon, item):
            job_ref.set_margin_top_percent(percent)
            _persist_job_settings(job_ref)
            logging.info("Top margin set to %s%%", percent)
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"顶边 {percent:g}%",
            on_select,
            checked=lambda item: job_ref.margin_top_percent == percent,
            radio=True,
        )

    def make_margin_bottom_item(percent: float):
        def on_select(icon, item):
            job_ref.set_margin_bottom_percent(percent)
            _persist_job_settings(job_ref)
            logging.info("Bottom margin set to %s%%", percent)
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"底边 {percent:g}%",
            on_select,
            checked=lambda item: job_ref.margin_bottom_percent == percent,
            radio=True,
        )

    global icon
    icon = pystray.Icon(f"{PROGRAM_NAME}_tray_icon")
    icon.icon = create_image()

    def refresh_tray_display() -> None:
        """刷新悬停标题，并重建菜单（Win32 会缓存，需 update_menu 才能看到新时间）。"""
        icon.title = format_tray_icon_title(
            job_ref.applied_observation_time,
            pixel_side=job_ref.applied_pixel_side,
        )
        icon.update_menu()

    resolution_menu = pystray.Menu(*[make_resolution_item(res) for res in IMAGE_RESOLUTION])
    margin_menu = pystray.Menu(
        pystray.MenuItem(
            "启用黑边修边",
            on_toggle_adjust,
            checked=lambda item: job_ref.auto_adjust,
        ),
        pystray.Menu.SEPARATOR,
        *[make_margin_top_item(p) for p in MARGIN_PERCENT_CHOICES],
        pystray.Menu.SEPARATOR,
        *[make_margin_bottom_item(p) for p in MARGIN_PERCENT_CHOICES],
    )
    log_menu = pystray.Menu(
        pystray.MenuItem(
            "启用日志",
            on_toggle_logging,
            checked=lambda item: is_logging_enabled(),
        ),
        pystray.MenuItem("打开日志文件", on_open_log),
    )
    about_menu = pystray.Menu(
        pystray.MenuItem("打开程序所在目录", on_open_program_dir),
        pystray.MenuItem("GitHub", on_open_github),
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
        pystray.MenuItem("检查更新", on_check_update),
    )

    def wallpaper_time_local_text(_item):
        obs_time = job_ref.applied_observation_time
        if not obs_time:
            return "壁纸时间（本地）：尚未应用"
        try:
            local = format_observation_local_time(obs_time)
        except (ValueError, OSError):
            logging.exception("Failed to convert observation time to local: %s", obs_time)
            return "壁纸时间（本地）：—"
        return f"壁纸时间（本地）：{local}"

    def wallpaper_time_utc_text(_item):
        obs_time = job_ref.applied_observation_time
        if obs_time:
            return f"壁纸时间（UTC）：{obs_time}"
        return "壁纸时间（UTC）：尚未应用"

    icon.menu = pystray.Menu(
        pystray.MenuItem(wallpaper_time_local_text, None),
        pystray.MenuItem(wallpaper_time_utc_text, None),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("立即更新壁纸", on_update_wallpaper),
        pystray.MenuItem(
            "暂停更新壁纸",
            on_toggle_pause,
            checked=lambda item: is_paused(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("图片分辨率", resolution_menu),
        pystray.MenuItem("黑边修边", margin_menu),
        pystray.MenuItem(
            "自动清理图片缓存",
            on_toggle_cleanup,
            checked=lambda item: job_ref.cleanup_after_apply,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "开机启动",
            on_startup,
            checked=lambda item: is_startup_set(),
        ),
        pystray.MenuItem("日志", log_menu),
        pystray.MenuItem("关于", about_menu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_quit),
    )

    job_ref.set_on_applied(refresh_tray_display)
    refresh_tray_display()
    icon.run_detached()
