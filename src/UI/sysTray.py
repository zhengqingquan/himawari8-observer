import pystray
import webbrowser
from tkinter import messagebox
from PIL import Image, ImageDraw
from src.event.event import end_main_sys
from src.metadata.soft_config import IMAGE_RESOLUTION
from src.metadata.soft_info import *
from src.startup import add_to_startup_exe, remove_from_startup_exe, is_startup_set

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
        pystray.MenuItem("更新壁纸", on_startup),
        pystray.MenuItem("暂停更新壁纸", on_startup), # 暂停更新壁纸，开始更新壁纸。
        pystray.MenuItem("图片分辨率", sub_menu), # 子菜单项
        pystray.MenuItem("开机启动", on_startup),
        pystray.MenuItem("日志设置", on_startup), # 记录日志 日志等级
        pystray.MenuItem(f"访问官网", on_offical_website),
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
        pystray.MenuItem("退出", on_quit)
    )

    # 启动图标。
    icon.run_detached()

    show_startup_notification()
