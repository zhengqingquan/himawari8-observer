# 可以使用多线程提升下载速度
# 拖慢下载速度是因为每次都需要重新
import requests
import time
import os
from lxml import etree
import logging
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def dl_dic_pic(pic, request):
    """
    根据dic进行下载，从传入的图片pic，获取下载所需的dic。
    :param pic:图片
    :param request:连接请求
    :return:下载完成返回True，下载未完成返回False
    """
    print("下载开始。")
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = True  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    dl_count = 1  # 计数值，正在下载第张图片
    file_size = 0  # 计数值，已经写入的文件大小
    chunk_size = 1024  # 每次下载的块大小

    # 设置重试策略
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    request.mount('http://', adapter)
    request.mount('https://', adapter)

    for url, path in pic.dic.items():
        file_path = os.path.abspath(path[0])  # 查看下载时的绝对路径
        print(f"正在下载第{dl_count}张图片。")
        print(f"当前下载的url为：{url}")
        print(f"当前下载的path为：{file_path}")

        r = request.get(url, verify=verify, proxies=proxies, stream=stream, timeout=(5, 14))
        print(f"请求状态为：{r.status_code}")

        pic_size = r.headers['Content-Length']  # 预下载的文件大小。单位：B（字节）
        size_K = round(int(pic_size) / 1024, 2)  # 预下载的文件大小。单位：K，保留两位小数
        size_M = round(int(size_K) / 1024, 2)  # 预下载的文件大小。单位：M，保留两位小数
        print(f"正在下载,文件大小为：{size_K}K（{pic_size}B）（{size_M}M）")

        # 开始下载，并且每次最多写入1024 B 的数据。
        if r.status_code is 200:
            with open(path[0], "wb") as file:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    file_size += len(chunk)
                    print(f"\r{file_size}/{pic_size}", end='')
                # 判断某张碎图是否下载完成。
                if file_size == int(pic_size):
                    pic.dic[url][1] = 1  # 则将其置为1，表示这张图片下载完成。
                    print(f"第{dl_count}张图片写入完成\n")
                file_size = 0
            dl_count += 1
            # print(f"\r已下载完成：{dl_count}/{pic.pic_chip}。", end="")

    # 验证是不是所有碎片图片都下载完成
    if pic.download_finish():
        print("图片全部下载完成！")
    else:
        print("未下载完成！")
    return pic.dl_finish_equal


def dl_post_pic(pic, request):
    """
    根据图片，使用完整下载方式，发送post请求下载图片。
    参考：
    https://blog.csdn.net/jiangshangchunjiezi/article/details/104488225/
    :param pic:图片
    :param request:连接请求
    :return:下载完成返回True，下载未完成返回False
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 开启验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    res = request.get(url=pic.hash_base, proxies=proxies)
    html = etree.HTML(res.content.decode("utf-8"))
    value_hash = html.xpath('//*[@id="fixedToken"]/@value')[0]  # 获取hash值。
    pic.post_data["data[FileSearch][fixedToken]"] = value_hash

    # 开始下载图片
    file_size = 0  # 已经写入的文件大小
    chunk_size = 1024  # 下载的块大小
    res = request.post(url=pic.sc_nc_web_base, data=pic.post_data, verify=verify, proxies=proxies, stream=stream)
    print(f"请求状态为：{res.status_code}")
    pic_size = res.headers['Content-Length']  # 预下载的文件大小。单位：B（字节）
    size_K = round(int(pic_size) / 1024, 2)  # 预下载的文件大小。单位：K，保留两位小数
    size_M = round(int(size_K) / 1024, 2)  # 预下载的文件大小。单位：M，保留两位小数
    print(f"正在下载,文件大小为：{size_K}K（{pic_size}B）（{size_M}M）")
    if res.status_code is 200:
        with open(pic.final_path_cpl, "wb") as file:
            for chunk in res.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                file_size += len(chunk)
                print(f"\r{file_size}/{pic_size}", end='')
                # TODO 写入日志
            # 判断是否下载完成。
            if file_size == int(pic_size):
                pic.dl_finish_cpl = True
                print("\n下载完成！")
    return pic.dl_finish_cpl


def dl_pic(url, path):
    """
    根据一个url下载图片，用于单张图片的下载。默认关闭代练，关闭验证SSL证书。
    :param url:下载图片的url
    :param path:图片保存的路径，包括名称。
    :return: None
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    time_dl_start = time.process_time()
    print("开始下载。")
    r = requests.Session().get(url, verify=verify, proxies=proxies, stream=stream)  # 让request保持连接
    size = r.headers['Content-Length']  # 文件大小。单位：字节
    size_K = round(int(size) / 1024)
    size_M = round(int(size_K) / 1024, 2)
    link_status = r.status_code  # 响应请求状态
    chunk_size = 1024  # 下载的块大小
    print(f"下载的文件大小为：{size}B   {size_K}K   {size_M}M")  # 下载的文件大小
    with open(path, "wb") as file:
        file.write(r.content)
    print("下载完成")
    time_dl_over = time.process_time()
    process_time = time_dl_over - time_dl_start
    print("下载时间为：" + str(process_time))


def dl_pic_2(url, path):
    """
    download picture
    用于下载图片，默认关闭代练，关闭验证SSL证书。
    :param url:下载图片的url
    :param path:图片保存的路径，包括名称。
    :return: None
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False

    time_dl_start = time.perf_counter()
    print("开始下载。。。")
    r = requests.Session().get(url, verify=verify, proxies=proxies, stream=stream)  # 让request保持连接
    time_dl_request = time.perf_counter()
    requests_tiem = time_dl_request - time_dl_start
    print("请求时间为：" + str(requests_tiem))
    size = r.headers['Content-Length']  # 文件大小。单位：字节
    size_K = round(int(size) / 1024)
    size_M = round(int(size_K) / 1024, 2)
    link_status = r.status_code  # 响应请求状态
    chunk_size = 1024  # 下载的块大小
    print(f"下载的文件大小为：{size}B   {size_K}K   {size_M}M")  # 下载的文件大小
    count = 0
    with open(path, "wb") as file:
        for chunk in r.iter_content(chunk_size=chunk_size):
            # file.write(r.content(chunk_size))
            file.write(chunk)
            # count += len(chunk)
            count += 1
            print(f"{count}B", end="\r")
            # file.write(r.content)
    print("\n下载完成")
    time_dl_over = time.perf_counter()
    process_time = time_dl_over - time_dl_start
    print("下载时间为：" + str(process_time))


if __name__ == '__main__':
    # temp_url = "https://himawari8.nict.go.jp/img/D531106/thumbnail/550/2021/05/18/023000_0_0.png"
    # temp_path = "../test/temp.png"
    # dl_pic_2(temp_url, temp_path)
    # 无网络会报requests.exceptions.ConnectionError错误。
    from cls.Pic import *
    from cls import Pic
    from tool.tool import *
    from dl.dlinit import *

    # from dl.dlpic import *

    requester = dl_init()
    last_time = get_last_time(requester)
    pic = Pic(last_time, "20d")  # 实例化类
    dl_post_pic(pic, requester)
