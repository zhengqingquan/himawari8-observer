# 可以使用多线程提升下载速度
# 拖慢下载速度是因为每次都需要重新
import time

import requests


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
            file.write(chunk)
            count += 1
            print(f"{count}B", end="\r")
    print("\n下载完成")
    time_dl_over = time.perf_counter()
    process_time = time_dl_over - time_dl_start
    print("下载时间为：" + str(process_time))


if __name__ == "__main__":
    from cls.Pic import Pic
    from dl.dlinit import dl_init, get_last_time

    requester = dl_init()
    last_time = get_last_time(requester)
    pic = Pic(last_time, "20d")
    dl_dic_pic(pic, requester)
