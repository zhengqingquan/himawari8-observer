"""
创建文件夹
"""

import os
import logging
from src.pic.Pic import Pic


def arr_create_folder(arr):
    """
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
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def cls_create_folder(pic: Pic):
    """
    根据参数传入的pic类创建文件夹。
    :param pic:Pic类，表示照片
    :return:None
    """
    arr_create_folder(pic.arr_puzzle)  # 创建碎片文件夹。
    create_folder(pic.folder_path)  # 创建complete文件夹。
    logging.info("文件夹folder构建完成。")
