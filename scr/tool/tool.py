"""
一些工具函数
"""
import sys
from _datetime import datetime
from datetime import datetime
from time import strftime
from tool.folder import *


def get_system_time():
    """
    Finish
    获取当前系统的时间。
    :return:返回一个datetime.datetime类。如果需要，可以调用返回值的curr_time.year来获取系统时间的年份,且值为int型。
    """
    curr_time = datetime.now()
    return curr_time


def get_win():
    """
    TODO:除了Windows和Mac系统，也应该可以检测其他系统的环境
    获取系统环境
    :return:不同系统的系统名称。类型为字符串str
    """
    if sys.platform in ["win32", "cygwin"]:
        return "windows"
    elif sys.platform == "darwin":
        return "mac"
    else:
        return "unknown"  # 其他系统


def print_arr(arr):
    """
    Finish
    用于打印数组的元素内容和数组的个数。
    :param arr:数组
    :return:None
    """
    for element in arr:
        print(element)
    print(f"数组的长度为：{len(arr)}")


def print_dic(dic):
    """
    用于打印字典中url和path对应的内容，和字典元素的个数。
    :param dic:字典，内容是url和path的映射
    :return:None
    """
    for url, path in dic.items():
        print(url)
        print(path)
    print(f"字典的长度为：{len(dic)}")


def time_dic(time, equal_int):
    """
    Finish
    将时间和碎片整合成一个字典类型。
    :param time:时间
    :param equal_int:碎片
    :return:字典类型。
    """
    year = strftime("%Y", time)
    month = strftime("%m", time)
    day = strftime("%d", time)
    hour = strftime("%H", time)
    minute = strftime("%M", time)
    seconds = strftime("%S", time)
    dic_info = {
        "equal_str": equal_int,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "seconds": seconds
    }
    return dic_info


def time_zones():
    """
    TODO:这里可能需要进行时区的换算。
    :return:
    """
    pass


def time_to_url_1d(time):
    """
    根据时间获取550分辨率的url。默认1d
    :param time:类型是time.struct_time类
    :return:
    """
    year = strftime("%Y", time)
    month = strftime("%m", time)
    day = strftime("%d", time)
    hour = strftime("%H", time)
    minute = strftime("%M", time)
    seconds = strftime("%S", time)
    url = f"https://himawari8.nict.go.jp/img/D531106/1d/550/{year}/{month}/{day}/{hour}{minute}{seconds}_0_0.png"


def time_to_url(time, equal="20d"):
    """
    将获得的时间转换为正确的下载url
    :param time:类型是time.struct_time类
    :return:下载的url
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
    # pic_name = f"{hour}{minute}{seconds}_{locationX}_{locationY}.png"
    arr_url = []
    while locationY < 20:
        while locationX < 20:
            url = f"https://himawari8.nict.go.jp/img/D531106/{equal}/550/{year}/{month}/{day}/{hour}{minute}{seconds}_{locationX}_{locationY}.png"
            arr_url.append(url)
            locationX = locationX + 1
        locationX = 0
        locationY = locationY + 1
    print("下载链接url构建完成。")
    return arr_url


def time_to_path(time, equal="20d"):
    """
    获取的时间转换为文件路径。
    :param time: 类型是time.struct_time类
    :param equal:
    :return:
    """
    equal = equal
    locationY = 0
    locationX = 0
    year = strftime("%Y", time)
    month = strftime("%m", time)
    day = strftime("%d", time)
    hour = strftime("%H", time)
    minute = strftime("%M", time)
    seconds = strftime("%S", time)
    arr_path = []
    while locationY < 20:
        while locationX < 20:
            pic_name = f"{hour}{minute}{seconds}_{locationX}_{locationY}.png"
            path = f"../img/{year}{month}{day}{hour}{minute}{seconds}/{equal}/{locationY}/{pic_name}"
            arr_path.append(path)
            locationX = locationX + 1
        locationX = 0
        locationY = locationY + 1
    print("下载路径path构建完成。")
    return arr_path


def dic_url_path(arr_url, arr_path):
    """
    将下载的url和路径对应起来。某张图片应该下载到某个地方，做一个映射。
    :param arr_url:图片的下载url，类型是数组。
    :param arr_path:图片的存放路径，类型是数组。
    :return:返回url和路径的映射字典。
    """
    dic = dict(zip(arr_url, arr_path))
    print("url和path的映射字典构建完成")
    return dic


if __name__ == '__main__':
    import dl.dlinit

    r = dl.dlinit.dl_init()
    time_temp = dl.dlinit.get_last_time(r)
    print(time_temp)
    arr = time_to_url(time_temp)
    arr_path = time_to_path(time_temp)
    dica = dic_url_path(arr, arr_path)
    # print(dica)
    # print(dica.values())
    # dica.items()
    for element, path in dica.items():
        print(element)
        print(path)
    # get_system_time()
    # for index, element in enumerate(['hello', 'world']):
    #     print(index)
    #     print(element)
    pass
