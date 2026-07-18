import logging
import os
import threading

import pystray
import webbrowser
from tkinter import messagebox
from PIL import Image, ImageDraw
from src.event.event import end_main_sys
from src.metadata.soft_config import IMAGE_RESOLUTION, LOG_PATH
from src.metadata.soft_info import DESCRIPTION, PROGRAM_NAME, SOFTWARE_VERSION, WEBSITE
from src.startup import add_to_startup_exe, remove_from_startup_exe, is_startup_set
from src.wallpaper_job import WallpaperJobRef
from src.wallpaper_update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)


# 创建一个函数来绘制托盘图标
def create_image():
    # 创建一个空白图像
    image = Image.new("RGB", (64, 64), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    # 在图像中绘制一个黑色的圆圈
    dc.ellipse((16, 16, 48, 48), fill="black")
    return image


# 创建托盘图标右键菜单的回调函数
def on_clicked(icon, item):
    message_text = f"""\
软件：{PROGRAM_NAME}
版本：{SOFTWARE_VERSION}
介绍：{DESCRIPTION}
"""
    messagebox.showinfo("信息", message_text)


# 创建托盘图标右键菜单的回调函数
def on_quit(icon, item):
    icon.stop()
    end_main_sys()


# 启动时的提示。
def show_startup_notification():
    # TODO 使用通知而非弹窗的效果会好一些。
    # messagebox.showinfo("信息", f"{PROGRAM_NAME} {SOFTWARE_VERSION} 启动成功。")
    pass


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
    """job_ref: 托盘与定时器共享的壁纸任务引用，由 run.py 注入。"""

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

    global icon
    icon = pystray.Icon(f"{PROGRAM_NAME}_sysTray_icon")
    icon.icon = create_image()
    icon.title = PROGRAM_NAME

    sub_menu = pystray.Menu(*[make_resolution_item(res) for res in IMAGE_RESOLUTION])

    icon.menu = pystray.Menu(
        pystray.MenuItem("更新壁纸", on_update_wallpaper),
        pystray.MenuItem(pause_menu_text, on_toggle_pause),
        pystray.MenuItem("图片分辨率", sub_menu),
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

    show_startup_notification()
