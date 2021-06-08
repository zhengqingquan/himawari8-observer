"""
试着用post请求直接下载
https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV
"""
import requests
from lxml import etree
from dl.dlinit import dl_init


def post_requests(request):
    proxies = {'http': None, 'https': None}  # 不使用代理
    file_size = 0  # 已经写入的文件大小
    chunk_size = 1024  # 下载的块大小
    verify = True  # 开启验证SSL证书
    stream = True  # 不会立马开始下载，默认是False
    path = "C:/Users/96400/Downloads/post.png"
    # HASH = "bb32dee6b4fde5a60f7f336c7ce361189d96b676"
    url = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/fileSearch/download"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Length": "462",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "_ga=GA1.3.494186484.1620632701; _gid=GA1.3.1241868910.1620805755; CAKEPHP=0j34ft0iisbe3p647a0j8993giaim2p92l24j2g7ifn6330vk3s1",
        "Host": "sc-nc-web.nict.go.jp",
        "Origin": "https://sc-nc-web.nict.go.jp",
        "Referer": "https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV",
        "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google Chrome\";v=\"90\"",
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    data = {"_method": "POST",
            "data[FileSearch][is_compress]": "false",
            "data[FileSearch][fixedToken]": get_hash(request),
            "data[FileSearch][hashUrl]": "bDw2maKV",
            "action": "dir_download_dl",
            "filelist[0]":
                "/osn-disk/webuser/wsdb/share_directory/bDw2maKV/png/Pifd/2021/06-08/02/hima820210608022000fd.png",
            "dl_path":
                "/osn-disk/webuser/wsdb/share_directory/bDw2maKV/png/Pifd/2021/06-08/02/hima820210608022000fd.png"
            }
    print(f'hash值为：{data.get("data[FileSearch][fixedToken]")}')
    # headers有问题，无法使用
    # res = request.post(url=url, headers=headers, data=data, verify=verify, proxies=proxies, stream=stream)
    res = request.post(url=url, data=data, verify=verify, proxies=proxies, stream=stream)
    print(f"请求状态为：{res.status_code}")
    if res.status_code is 200:
        with open(path, "wb") as file:
            for chunk in res.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                file_size += len(chunk)


def get_hash(request):
    """
    Finish
    获取hash值
    :return:hash值，str类型。
    """
    proxies = {'http': None, 'https': None}  # 不使用代理
    url = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV"
    res = request.get(url=url, proxies=proxies)
    # print(res.text)  # 用来打印整个网页的html
    # print(res.content.decode("utf-8"))  # 用来打印整个网页的html
    html = etree.HTML(res.content.decode("utf-8"))
    value_hash = html.xpath('//*[@id="fixedToken"]/@value')[0]  # 获取hash值。
    return str(value_hash)


if __name__ == '__main__':
    request = dl_init()
    post_requests(request)
