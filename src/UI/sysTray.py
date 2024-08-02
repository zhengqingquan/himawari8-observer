from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
from src.event.event import end_main_sys

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
    messagebox.showinfo("信息", "您点击了托盘图标菜单项")

# 创建托盘图标右键菜单的回调函数
def on_quit(icon, item):
    icon.stop()
    end_main_sys()

# 创建托盘图标
def setup_tray_icon():
    global icon
    icon = pystray.Icon("test_icon")
    icon.icon = create_image()
    icon.title = "系统托盘图标"
    icon.menu = pystray.Menu(
        pystray.MenuItem("显示消息", on_clicked),
        pystray.MenuItem("退出", on_quit)
    )
    icon.run()
