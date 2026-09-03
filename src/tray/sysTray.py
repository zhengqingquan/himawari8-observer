import logging
import os
import sys
import threading
import ctypes
from pathlib import Path

import pystray
import webbrowser
from PIL import Image
from src.event.event import end_main_sys
from src.metadata.soft_config import IMAGE_RESOLUTION, LOG_PATH, MARGIN_PERCENT_CHOICES
from src.metadata.soft_info import DESCRIPTION, PROGRAM_NAME, SOFTWARE_VERSION, WEBSITE
from src.startup import add_to_startup_exe, remove_from_startup_exe, is_startup_set
from src.wallpaper.job import WallpaperJobRef
from src.wallpaper.update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)

_TRAY_ICON_NAME = "tray_icon.png"


def _tray_icon_path() -> Path:
    """打包后从 _MEIPASS/assets 读；开发时从仓库 assets/ 读。"""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "assets" / _TRAY_ICON_NAME
            if bundled.is_file():
                return bundled
    return Path(__file__).resolve().parents[2] / "assets" / _TRAY_ICON_NAME


def create_image():
    return Image.open(_tray_icon_path())


# 创建托盘图标右键菜单的回调函数
def on_clicked(icon, item):
    message_text = f"""\
软件：{PROGRAM_NAME}
版本：{SOFTWARE_VERSION}
介绍：{DESCRIPTION}
"""

    def show_about():
        # 独立线程弹出，避免卡住 pystray 的 Win32 消息循环。
        # MB_OK | MB_ICONINFORMATION | MB_TOPMOST | MB_SETFOREGROUND
        ctypes.windll.user32.MessageBoxW(
            None,
            message_text,
            f"关于 {PROGRAM_NAME}",
            0x00050040,
        )

    threading.Thread(target=show_about, daemon=True).start()


# 创建托盘图标右键菜单的回调函数
def on_quit(icon, item):
    icon.stop()
    end_main_sys()


# 打开官网菜单项的回调函数。
def on_offical_website(icon, item):
    webbrowser.open_new(WEBSITE)


# 开机启动菜单项的回调函数。
def on_startup(icon, item):
    # TODO 需要判断是否有同名的，但执行路径不一样的，若有就删掉重新设置。
    if is_startup_set():
        remove_from_startup_exe()
    else:
        add_to_startup_exe()


def on_open_log(icon, item):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.touch(exist_ok=True)
    os.startfile(LOG_PATH)


# 创建托盘图标
def setup_tray_icon(job_ref: WallpaperJobRef):
    """job_ref: 托盘与定时器共享的壁纸任务引用，由 src.app 注入。"""

    def on_update_wallpaper(icon, item):
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def pause_menu_text(item):
        return "恢复更新壁纸" if is_paused() else "暂停更新壁纸"

    def on_toggle_pause(icon, item):
        if is_paused():
            resume()
        else:
            pause()

    def make_resolution_item(pixel_side: int):
        def on_select(icon, item):
            job_ref.set_pixel_side(pixel_side)
            logging.info("分辨率档位已切换为 %spx（%s）", pixel_side, job_ref.resolution_grade)
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
        logging.info("黑边修边已%s", "开启" if enabled else "关闭")
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def on_toggle_cleanup(icon, item):
        enabled = not job_ref.cleanup_after_apply
        job_ref.set_cleanup_after_apply(enabled)
        logging.info("应用后清理缓存已%s", "开启" if enabled else "关闭")

    def make_margin_top_item(percent: float):
        def on_select(icon, item):
            job_ref.set_margin_top_percent(percent)
            logging.info("顶边黑边已设为 %s%%", percent)
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
            logging.info("底边黑边已设为 %s%%", percent)
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
    icon = pystray.Icon(f"{PROGRAM_NAME}_sysTray_icon")
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

    icon.menu = pystray.Menu(
        pystray.MenuItem("更新壁纸", on_update_wallpaper),
        pystray.MenuItem(pause_menu_text, on_toggle_pause),
        pystray.MenuItem("图片分辨率", resolution_menu),
        pystray.MenuItem("黑边修边", margin_menu),
        pystray.MenuItem(
            "应用后清理缓存",
            on_toggle_cleanup,
            checked=lambda item: job_ref.cleanup_after_apply,
        ),
        pystray.MenuItem(
            "开机启动",
            on_startup,
            checked=lambda item: is_startup_set(),
        ),
        pystray.MenuItem("打开日志", on_open_log),
        pystray.MenuItem("访问官网", on_offical_website),
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
        pystray.MenuItem("退出", on_quit),
    )

    # 启动图标。
    icon.run_detached()
