"""
下载的初始化
"""
import requests
import json
from time import strptime
import time
 

def test_request(times=20):
    """
    Finish
    用于测试连接速度。
    :param times: 连接的次数，默认20次。
    :return:None
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    url = "https://himawari8.nict.go.jp/img/D531106/thumbnail/550/2021/05/18/023000_0_0.png"
    time_dl_start = time.perf_counter()  # 开始时间
    r = requests.Session()  # 让request保持连接
    temp = 1
    while temp < times:
        print(f"第{temp}次连接")
        r.get(url, verify=verify, proxies=proxies, stream=stream)
        temp = temp + 1
    time_dl_over = time.perf_counter()  # 结束时间
    print(f"使用时间为：{time_dl_over-time_dl_start}")


def dl_init():
    """
    Finish
    参考：https://www.cnblogs.com/tianleblog/p/11496177.html
    :return:返回一个连接对象
    """
    requester = requests.Session()  # 为了让request保持连接
    return requester


def get_last_time(request):
    """
    Finish
    获取最新的时间。
    :param request:开启的连接对象
    :return:返回一个时间对象，time.struct_time类型，格式为%Y-%m-%d %H:%M:%S，对应为2021-05-21 03:10:00
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    url = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"
    response = request.get(url, verify=verify, proxies=proxies, stream=stream)
    latest_json = response.content
    # print(latest_json)
    latest_time = strptime(json.loads(latest_json.decode("utf-8"))["date"], "%Y-%m-%d %H:%M:%S")
    print("当前时间为：" + json.loads(latest_json.decode("utf-8"))["date"])
    # print(latest_time)
    # print(type(latest_time))
    return latest_time


if __name__ == '__main__':
    requester = dl_init()
    get_last_time(requester)
    test_request()
