# 可以使用多线程提升下载速度
# 拖慢下载速度是因为每次都需要重新
import requests
import time
import os


def dl_dic_pic(pic, request):
    print("下载开始。")
    proxies = {'http': None, 'https': None}  # 不使用代理
    verify = False  # 关闭验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    dl_count = 0  # 下载到第几个的计数值
    file_size = 0  # 已经写入的文件大小
    chunk_size = 1024  # 下载的块大小
    for url, path in pic.dic.items():
        file_path = os.path.abspath(path[0])
        r = request.get(url, verify=verify, proxies=proxies, stream=stream)

        size = r.headers['Content-Length']  # 预下载的文件大小。单位：B（字节）
        size_K = round(int(size) / 1024, 2)  # 预下载的文件大小。单位：K
        size_M = round(int(size_K) / 1024, 2)  # 预下载的文件大小。单位：M

        print(f"正在下载第{dl_count+1}张图片。")
        # print(f"开始请求序号为：{dl_count}")
        print(f"当前下载的url为：{url}")
        print(f"当前下载的path为：{file_path}")
        print(f"请求状态为：{r.status_code}")
        print(f"正在下载,文件大小为：{size_K}k（{size}B）")

        # 开始下载，并且每次最多写入1024 B 的数据。
        with open(path[0], "wb") as file:
            for chunk in r.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                file_size += len(chunk)
                print(file_size)
            # 判断某张碎图是否下载完成。
            if file_size == int(size):
                pic.dic[url][1] = 1
                print(f"序号{dl_count}写入完成\n")
            file_size = 0
        dl_count += 1
        # print(f"\r已下载完成：{dl_count}/{pic.pic_chip}。", end="")
    if pic.download_finish():
        print("图片全部下载完成！")
    else:
        print("未下载完成！")


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
    # 无网络会报requests.exceptions.ConnectionError错误。
    # test_request()
