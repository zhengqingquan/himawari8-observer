"""
下载的初始化
"""
import requests
import json
from time import strptime


def dl_init():
    requester = requests.Session()  # 让request保持连接
    return requester


def get_last_time(request):
    """
    获取最新的时间。
    :param request:开启的连接对象
    :return:返回一个时间对象
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    url = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json"
    response = request.get(url, verify=verify, proxies=proxies, stream=stream)
    latest_json = response.content
    latest_time = strptime(json.loads(latest_json.decode("utf-8"))["date"], "%Y-%m-%d %H:%M:%S")
    # print(latest_time)
    # print(latest_time.tm_hour)
    return latest_time


if __name__ == '__main__':
    r = dl_init()
    get_last_time(r)
    pass
