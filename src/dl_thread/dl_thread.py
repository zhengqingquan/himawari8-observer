"""
创建下载的线程
"""
import threading
import multiprocessing
import time

# 获取电脑有多少个逻辑处理器（线程）
num_cpus = multiprocessing.cpu_count()
print(num_cpus)

# 线程数
thread_num = num_cpus
# 信号量，同时只允许3个线程运行
threading.BoundedSemaphore(thread_num)

# 当前运行线程的名字
def loop():
    while True:
        time.sleep(5)
        print(threading.current_thread().name)


# for i in range(0, thread_num):
#     t = threading.Thread(target=loop)
#     t.start()

# # for i in range(0, thread_num):
# #     t = threading.Thread(target=loop, name=f"LoopThread {i}")
# #     t.start()
# print(range(0, thread_num))

import sys
try:
    for i in range(0, thread_num):
        t = threading.Thread(target=loop)
        t.start()
except KeyboardInterrupt:
    sys.exit()