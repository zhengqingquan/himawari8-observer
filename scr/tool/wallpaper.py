"""
更换window桌面
"""
import os
from os import listdir
from os.path import isfile, join
import ctypes


# # 找某个文件的绝对路径
# # 一般用于把相对路径转为绝对路径
# file_path = os.path.abspath("frames")
# print(file_path)
#
# # 遍历特定文件夹
# file = [filename for filename in listdir(file_path) if isfile(join(file_path, filename))]
# print(file)
#
# # 路径拼接，
# image_path = os.path.join(file_path, "hima820210510153000fd.png")
# print(type(image_path))
# print(image_path)


def pic_wallpaper(pic):
    """
    根据传入的图片替换桌面背景。
    :param pic:类pic
    :return:
    """
    print("正在更换桌面。")
    path_wallpaper(os.path.abspath(pic.final_path))


def path_wallpaper(wallpaper_path):
    """
    Finish
    根据路径替换桌面背景，win7不支持png格式。
    :param wallpaper_path:图片的绝对路径，若不是绝对路径回默认为纯色（黑）背景
    :return:
    """
    print("正在更换桌面。")
    temp = ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 0)
    if temp is 1:
        print("桌面更换成功。")
    else:
        print("桌面更换失败。")


if __name__ == "__main__":
    path = 'C:\\Users\\96400\\Downloads\\154000_0_0.png'
    path = 'C:/Users/96400/Downloads/154000_0_0.png'
    # path = "..img/20210607011000/complete/20d20210607011000.png"
    path_wallpaper(path)
