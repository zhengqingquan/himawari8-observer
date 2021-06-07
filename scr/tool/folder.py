"""
folder.py

创建文件夹
"""

import os
from time import strftime


def create_dic_folder(time, equal="20d"):
    """
    根据时间创建文件夹。
    :param time: 时间
    :param equal: 默认为20d
    :return:
    """
    equal = equal
    year = strftime("%Y", time)
    month = strftime("%m", time)
    day = strftime("%d", time)
    hour = strftime("%H", time)
    minute = strftime("%M", time)
    seconds = strftime("%S", time)
    locationY = 0
    locationX = 0
    while locationY < 20:
        while locationX < 20:
            create_folder(f"../img/{year}{month}{day}{hour}{minute}{seconds}/{equal}/{locationY}")
            locationX = locationX + 1
        locationX = 0
        locationY = locationY + 1
    print("文件夹folder构建完成。")


def arr_create_folder(arr):
    """
    Finish
    根据参数传入的数组创建文件夹
    :param arr:
    :return:None
    """
    for item in arr:
        create_folder(item)


def cls_create_folder(pic):
    """
    Finish
    根据参数传入的pic类创建文件夹。
    :param pic:Pic类，表示照片
    :return:None
    """
    arr_create_folder(pic.arr_puzzle)  # 创建碎片文件夹。
    create_folder(pic.folder_path)  # 创建complete文件夹。
    print("文件夹folder构建完成。")


def create_folder(folder_path):
    """
    Finish
    判断路径是否存在，若不存在则创建一个。
    :param folder_path:文件夹路径。判断文件夹是否存在，如果不存在则创建一个
    :return:None
    """
    is_exists = os.path.exists(folder_path)  # 用于判断文件夹是否存在（也可以判断某个文件）
    # print("文件夹是否存在：" + str(is_exists))

    # 用于创建文件夹，若已经存在会抛出FileExistsError
    if not is_exists:
        os.makedirs(folder_path)


if __name__ == "__main__":
    from dl.dlinit import *

    # 获取时间
    requester = dl_init()
    time_str = get_last_time(requester)
    create_dic_folder(time_str)  # 注意，在测试的时候路径为../../img/{year}{month}{day}{hour}{minute}{seconds}/{equal}/{locationY}
    pass
