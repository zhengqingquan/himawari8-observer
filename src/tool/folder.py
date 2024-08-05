"""
创建文件夹
"""

import os
from time import strftime
import logging
from src.cls.Pic import Pic

def create_dic_folder(time, equal="20d"):
    """
    根据时间创建文件夹。
    :param time: 时间
    :param equal: 默认为20d
    :return:
    """
    equal = equal
    year = strftime(r"%Y", time)
    month = strftime(r"%m", time)
    day = strftime(r"%d", time)
    hour = strftime(r"%H", time)
    minute = strftime(r"%M", time)
    seconds = strftime(r"%S", time)
    locationY = 0
    locationX = 0
    while locationY < 20:
        while locationX < 20:
            create_folder(f"../img/{year}{month}{day}{hour}{minute}{seconds}/{equal}/{locationY}")
            locationX = locationX + 1
        locationX = 0
        locationY = locationY + 1
    logging.info("文件夹folder构建完成。")


def arr_create_folder(arr):
    """
    Finish
    根据参数传入的数组创建文件夹
    :param arr:
    :return:None
    """
    for item in arr:
        create_folder(item)

def create_folder(folder_path):
    """
    判断路径是否存在，若不存在则创建一个。
    :param folder_path:文件夹路径。判断文件夹是否存在，如果不存在则创建一个
    :return:None
    """
    # os.path.exists 用于判断文件夹是否存在（也可以判断某个文件）
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def cls_create_folder(pic:Pic):
    """
    根据参数传入的pic类创建文件夹。
    :param pic:Pic类，表示照片
    :return:None
    """
    arr_create_folder(pic.arr_puzzle)  # 创建碎片文件夹。
    create_folder(pic.folder_path)  # 创建complete文件夹。
    logging.info("文件夹folder构建完成。")
