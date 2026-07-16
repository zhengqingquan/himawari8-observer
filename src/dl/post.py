"""
试着用post请求直接下载
https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV
"""

from lxml import etree
from dl.dlinit import dl_init


def post_requests(request):
    proxies = {"http": None, "https": None}  # 不使用代理
    verify = True  # 开启验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    # path = "C:/Users/96400/Downloads/post.png"
    # HASH = "bb32dee6b4fde5a60f7f336c7ce361189d96b676"
    url = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/fileSearch/download"
    # headers 有问题，无法使用；保留备查
    # headers = {
    #     "Accept": "...",
    #     "Content-Type": "application/x-www-form-urlencoded",
    #     ...
    # }
    data = {
        "_method": "POST",
        "data[FileSearch][is_compress]": "false",
        "data[FileSearch][fixedToken]": get_hash(request),
        "data[FileSearch][hashUrl]": "bDw2maKV",
        "action": "dir_download_dl",
        "filelist[0]": "/osn-disk/webuser/wsdb/share_directory/bDw2maKV/png/Pifd/2021/06-08/02/hima820210608022000fd.png",
        "dl_path": "/osn-disk/webuser/wsdb/share_directory/bDw2maKV/png/Pifd/2021/06-08/02/hima820210608022000fd.png",
    }
    print(f"hash值为：{data.get('data[FileSearch][fixedToken]')}")
    # headers有问题，无法使用
    # res = request.post(url=url, headers=headers, data=data, verify=verify, proxies=proxies, stream=stream)
    res = request.post(url=url, data=data, verify=verify, proxies=proxies, stream=stream)
    print(f"请求状态为：{res.status_code}")
    print(f"文件大小为：{res.headers['Content-Length']}")
    # if res.status_code == 200:
    #     file_size = 0
    #     chunk_size = 1024
    #     with open(path, "wb") as file:
    #         for chunk in res.iter_content(chunk_size=chunk_size):
    #             file.write(chunk)
    #             file_size += len(chunk)
    #             print(file_size)


def get_hash(request):
    """
    Finish
    获取hash值
    :return:hash值，str类型。
    """
    proxies = {"http": None, "https": None}  # 不使用代理
    url = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV"
    res = request.get(url=url, proxies=proxies)
    # print(res.text)  # 用来打印整个网页的html
    # print(res.content.decode("utf-8"))  # 用来打印整个网页的html
    html = etree.HTML(res.content.decode("utf-8"))
    value_hash = html.xpath('//*[@id="fixedToken"]/@value')[0]  # 获取hash值。
    return str(value_hash)


if __name__ == "__main__":
    request = dl_init()
    post_requests(request)
