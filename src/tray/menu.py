"""系统托盘菜单：分辨率、修边、暂停、开机启动、日志与关于。"""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from pathlib import Path

import pystray
import webbrowser
from PIL import Image

from src.event.event import request_shutdown
from src.log.log import is_logging_enabled, set_logging_enabled
from src.metadata.soft_config import IMAGE_RESOLUTION, LOG_PATH, MARGIN_PERCENT_CHOICES
from src.metadata.soft_info import DESCRIPTION, PROGRAM_NAME, SOFTWARE_VERSION, WEBSITE
from src.settings import save_settings, settings_dict_from_job
from src.startup import add_to_startup_exe, is_startup_set, remove_from_startup_exe
from src.wallpaper.job import WallpaperJobRef
from src.wallpaper.update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)

_TRAY_ICON_NAME = "tray_icon.png"


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
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
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
    icon.title = PROGRAM_NAME

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
        pystray.MenuItem("GitHub", on_open_github),
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
    )

    icon.menu = pystray.Menu(
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

    icon.run_detached()
