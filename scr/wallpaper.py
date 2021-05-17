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


def wallpaper(path):
    print("开始更换桌面。")
    temp = ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)
    if temp is 1:
        print("桌面更换成功。")
    else:
        print("桌面更换失败。")


if __name__ == "__main__":
    wallpaper('C:\\Users\\96400\\Downloads\\154000_0_0.png')
