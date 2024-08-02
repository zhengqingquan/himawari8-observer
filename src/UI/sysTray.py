from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
from src.event.event import end_main_sys
from src.head.config import IMAGE_RESOLUTION
from src.head.define import *
import webbrowser

# 创建一个函数来绘制托盘图标
def create_image():
    # 创建一个空白图像
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    # 在图像中绘制一个黑色的圆圈
    dc.ellipse((16, 16, 48, 48), fill='black')
    return image

# 创建托盘图标右键菜单的回调函数
def on_clicked(icon, item):
    message_text = f"""\
软件：{PROGRAM_NAME}
版本：{SOFTWARE_VERSION}
介绍：{DESCRIPTION}
"""
    messagebox.showinfo("信息", message_text)

# 创建托盘图标子菜单的回调函数
def on_submenu_item(icon, item):
    messagebox.showinfo("子菜单项", "您点击了子菜单项")

# 创建托盘图标右键菜单的回调函数
def on_quit(icon, item):
    icon.stop()
    end_main_sys()

def on_offical_website(icon, item):
    # 打开指定的网站
    webbrowser.open_new(WEBSITE)

def on_startup(icon, item):
    # 打开指定的网站
    # webbrowser.open_new(WEBSITE)
    pass

# 创建子菜单项的回调函数
def make_submenu_item(resolution):
    return pystray.MenuItem(f"分辨率 {resolution}", lambda icon, item: on_startup(icon, item))

# 创建托盘图标
def setup_tray_icon():
    global icon
    icon = pystray.Icon(f"{PROGRAM_NAME}_sysTray_icon")
    icon.icon = create_image()
    icon.title = PROGRAM_NAME

    # 创建子菜单项
    sub_menu_items = [make_submenu_item(res) for res in IMAGE_RESOLUTION]

    # 创建子菜单
    sub_menu = pystray.Menu(*sub_menu_items)

    # 创建主菜单
    icon.menu = pystray.Menu(
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
        pystray.MenuItem(f"访问官网", on_offical_website),
        pystray.MenuItem("图片分辨率", sub_menu),  # 子菜单项
        pystray.MenuItem("开机启动", on_startup),
        pystray.MenuItem("记录日志", on_startup),
        pystray.MenuItem("立即更新壁纸", on_startup),
        pystray.MenuItem("退出", on_quit)
    )

    # 启动图标。
    icon.run()
