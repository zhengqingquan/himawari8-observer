"""
main.py

主函数入口,写一些参数相关的东西。
"""

# !/usr/bin/env python

from pathlib import Path

from src.cls.Pic import Pic
from src.dl.dlinit import dl_init, get_last_time
from src.dl_thread.dl_thread import download_files
from src.picdeal.photofunia import cls_photo_composition
from src.tool.folder import cls_create_folder
from src.tool.wallpaper import path_wallpaper


def main():
    # 新建一个下载会话。
    requester = dl_init()

    # 获取最新的时间
    time_str = get_last_time(requester)

    # 实例化图片pic类
    main_pic = Pic(time_str, "4d")

    # 根据时间创建文件夹folder
    cls_create_folder(main_pic)

    # 进行碎片化下载
    # dl_dic_pic(main_pic, requester)
    download_files(main_pic.dic)

    # 合成图片
    cls_photo_composition(main_pic)

    # 修边
    # fix_pic(main_pic.final_path_equal,main_pic.pic_pixel,main_pic.final_path_equal)

    # 替换桌面
    path_wallpaper(Path(main_pic.final_path_equal))
