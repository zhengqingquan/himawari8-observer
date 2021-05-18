# 可以使用多线程提升下载速度
# 拖慢下载速度是因为每次都需要重新
import requests
import time


def dl_pic(url, path):
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
    time_dl_start = time.process_time()
    print("开始下载。。。")
    r = requests.Session().get(url, verify=verify, proxies=proxies, stream=stream)  # 让request保持连接
    print("下载完成")
    size = r.headers['Content-Length']  # 文件大小。单位：字节
    size_K = round(int(size) / 1024)
    size_M = round(int(size_K) / 1024, 2)
    link_status = r.status_code  # 响应请求状态
    chunk_size = 1024  # 下载的块大小
    print(f"下载的文件大小为：{size}B   {size_K}K   {size_M}M")  # 下载的文件大小
    with open(path, "wb") as file:
        print("正在写入")
        file.write(r.content)
    print("写入结束")
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
    with open(path, "wb") as file:
        file.write(r.content)
    print("下载完成")
    time_dl_over = time.perf_counter()
    process_time = time_dl_over - time_dl_start
    print("下载时间为：" + str(process_time))


def test_request():
    temp = 0
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    url = "https://himawari8.nict.go.jp/img/D531106/thumbnail/550/2021/05/18/023000_0_0.png"
    time_dl_start = time.perf_counter()
    r = requests.Session()
    while temp < 100:
        print(f"第{temp}次连接")
        r.get(url, verify=verify, proxies=proxies, stream=stream)  # 让request保持连接
        temp = temp + 1
    time_dl_over = time.perf_counter()
    print(f"使用时间为：{time_dl_over-time_dl_start}")


if __name__ == '__main__':
    temp_url = "https://himawari8.nict.go.jp/img/D531106/thumbnail/550/2021/05/18/023000_0_0.png"
    temp_path = "../test/temp.png"
    dl_pic_2(temp_url, temp_path)
    # 无网络会爆requests.exceptions.ConnectionError错误。
    # test_request()
