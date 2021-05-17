

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
    r = requests.Session().get(url, verify=verify, proxies=proxies)  # 让request保持连接
    print("下载的文件大小为：" + r.headers['Content-Length'] + "k")  # 下载的文件大小
    print("开始下载。。。")
    time_dl_start = time.process_time()
    with open(path, "wb") as file:
        file.write(r.content)
    time_dl_over = time.process_time()
    process_time = time_dl_over - time_dl_start
    print("下载完成")
    print("下载时间为："+str(process_time))
