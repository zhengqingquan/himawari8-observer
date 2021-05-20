"""
一些工具函数
"""
from time import strptime, strftime, mktime
from datetime import timedelta, datetime


# 需要把windows的地址变成不含“\”的字符串


# 可能需要把png转化成jpg格式。


def time_to_url(time, equal="20d"):
    """
    将获得的时间转换为正确的下载url
    :param time:
    :return:下载的url
    """
    # time.tm_year
    # time.tm_mon
    # time.
    # 这里可能需要进行时区的换算。
    # print(mktime(time))
    # print(datetime.fromtimestamp(mktime(time)))
    # print(datetime.fromtimestamp(mktime(time)).timetuple())
    print(strftime("%Y/%m/%d/%H%M%S", time))
    print(type(strftime("%m", time)))
    # url=f"{locationY}"
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
    return arr_url


if __name__ == '__main__':
    import dl.dlinit

    r = dl.dlinit.dl_init()
    time_temp = dl.dlinit.get_last_time(r)
    print(time_temp)
    arr=time_to_url(time_temp)
    for a in arr:
        print(a)
    pass
