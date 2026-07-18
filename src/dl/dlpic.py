# 可以使用多线程提升下载速度
# 拖慢下载速度是因为每次都需要重新
import requests
import time
from lxml import etree


def dl_dic_pic(pic, request):
    """
    遗留入口：转发到统一的瓦片下载 seam。
    request 保留以兼容旧调用签名，不再使用。
    :param pic:图片
    :param request:连接请求（未使用）
    :return:下载完成返回True，下载未完成返回False
    """
    from src.tile_download import download_tiles

    download_tiles(pic)
    return pic.download_finish()


def dl_post_pic(pic, request):
    """
    根据图片，使用完整下载方式，发送post请求下载图片。
    参考：
    https://blog.csdn.net/jiangshangchunjiezi/article/details/104488225/
    :param pic:图片
    :param request:连接请求
    :return:下载完成返回True，下载未完成返回False
    """
    pic.ensure_complete_download_fields()
    proxies = {"http": None, "https": None}  # 不使用代理
    verify = False  # 开启验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    res = request.get(url=pic.hash_base, proxies=proxies)
    html = etree.HTML(res.content.decode("utf-8"))
    value_hash = html.xpath('//*[@id="fixedToken"]/@value')[0]  # 获取hash值。
    pic.post_data["data[FileSearch][fixedToken]"] = value_hash

    # 开始下载图片
    file_size = 0  # 已经写入的文件大小
    chunk_size = 1024  # 下载的块大小
    res = request.post(
        url=pic.sc_nc_web_base, data=pic.post_data, verify=verify, proxies=proxies, stream=stream
    )
    print(f"请求状态为：{res.status_code}")
    pic_size = res.headers["Content-Length"]  # 预下载的文件大小。单位：B（字节）
    size_K = round(int(pic_size) / 1024, 2)  # 预下载的文件大小。单位：K，保留两位小数
    size_M = round(int(size_K) / 1024, 2)  # 预下载的文件大小。单位：M，保留两位小数
    print(f"正在下载,文件大小为：{size_K}K（{pic_size}B）（{size_M}M）")
    if res.status_code == 200:
        with open(pic.final_path_cpl, "wb") as file:
            for chunk in res.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                file_size += len(chunk)
                print(f"\r{file_size}/{pic_size}", end="")
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
    proxies = {"http": None, "https": None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    time_dl_start = time.process_time()
    print("开始下载。")
    r = requests.Session().get(
        url, verify=verify, proxies=proxies, stream=stream
    )  # 让request保持连接
    size = r.headers["Content-Length"]  # 文件大小。单位：字节
    size_K = round(int(size) / 1024)
    size_M = round(int(size_K) / 1024, 2)
    print(f"响应状态：{r.status_code}")
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
    proxies = {"http": None, "https": None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False

    time_dl_start = time.perf_counter()
    print("开始下载。。。")
    r = requests.Session().get(
        url, verify=verify, proxies=proxies, stream=stream
    )  # 让request保持连接
    time_dl_request = time.perf_counter()
    requests_tiem = time_dl_request - time_dl_start
    print("请求时间为：" + str(requests_tiem))
    size = r.headers["Content-Length"]  # 文件大小。单位：字节
    size_K = round(int(size) / 1024)
    size_M = round(int(size_K) / 1024, 2)
    chunk_size = 1024  # 下载的块大小
    print(f"响应状态：{r.status_code}")
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


if __name__ == "__main__":
    # temp_url = "https://himawari8.nict.go.jp/img/D531106/thumbnail/550/2021/05/18/023000_0_0.png"
    # temp_path = "../test/temp.png"
    # dl_pic_2(temp_url, temp_path)
    # 无网络会报requests.exceptions.ConnectionError错误。
    from cls.Pic import Pic
    from dl.dlinit import dl_init, get_last_time

    # from dl.dlpic import *

    requester = dl_init()
    last_time = get_last_time(requester)
    pic = Pic(last_time, "20d")  # 实例化类
    dl_post_pic(pic, requester)
