"""
创建下载的线程
"""
import threading
import multiprocessing
import time
import concurrent.futures
import requests

# # 获取电脑有多少个逻辑处理器（线程）
# num_cpus = multiprocessing.cpu_count()
# print(num_cpus)

# # 线程数
# thread_num = num_cpus
# # 信号量，同时只允许3个线程运行
# threading.BoundedSemaphore(thread_num)

# # 当前运行线程的名字
# def loop():
#     while True:
#         time.sleep(5)
#         print(threading.current_thread().name)


# import sys
# try:
#     for i in range(0, thread_num):
#         t = threading.Thread(target=loop)
#         t.start()
# except KeyboardInterrupt:
#     sys.exit()

# 假设这是你要下载的文件的URL列表
file_urls = [
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_0.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_1.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_2.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_0_3.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_0.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_1.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_2.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_1_3.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_2_0.png',
    'https://himawari8.nict.go.jp/img/D531106/4d/550/2024/08/05/082000_2_1.png',
]

# 下载文件的函数
def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

# 使用多线程下载文件
def download_files(urls):
    # 创建一个包含16个工作线程的线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        # 提交所有下载任务，并将future对象和对应的URL存储在字典中
        future_to_url = {executor.submit(download_file, url): url for url in urls}
        # 遍历所有已完成的future对象
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                # 获取任务结果
                data = future.result()
                print(f'{url} 下载完成')
            except Exception as exc:
                print(f'{url} 下载时出错: {exc}')

download_files(file_urls)