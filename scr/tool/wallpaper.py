"""
更换window桌面
"""
import os
import ctypes


def pic_wallpaper(pic):
    """
    Finish
    根据传入的图片替换桌面背景。
    :param pic:类pic
    :return:1 or 0
    """
    return path_wallpaper(os.path.abspath(pic.final_path))


def path_wallpaper(wallpaper_path):
    """
    Finish
    根据路径替换桌面背景，win7不支持png格式。必须使用绝对路径。
    :param wallpaper_path:图片的绝对路径，若不是绝对路径回默认为纯色（黑）背景
    :return:1 or 0
    """
    print("正在更换桌面。")
    temp = ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 0)
    if temp is 1:
        print("桌面更换成功。")
    else:
        print("桌面更换失败。")
    return temp


if __name__ == "__main__":
    path = 'C:\\Users\\96400\\Downloads\\154000_0_0.png'
    path = 'C:/Users/96400/Downloads/154000_0_0.png'
    path_wallpaper(path)
