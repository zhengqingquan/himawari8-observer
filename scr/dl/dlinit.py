"""
下载的初始化
"""
import requests
import json
from time import strptime


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
    :return:返回一个时间对象,格式为%Y-%m-%d %H:%M:%S，例如对应为2021-05-21 03:10:00
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
    # print(type(last_time))
    return latest_time


if __name__ == '__main__':
    requester = dl_init()
    get_last_time(requester)
