"""
创建下载的线程
"""
import threading
import multiprocessing

# 线程数
thread_num = 3
# 信号量，同时只允许3个线程运行
threading.BoundedSemaphore(thread_num)

# 获取电脑有多少个逻辑处理器（线程）
num_cpus = multiprocessing.cpu_count()
print(num_cpus)


# 当前运行线程的名字
def loop():
    while True:
        print(threading.current_thread().name)


for i in range(0, thread_num):
    t = threading.Thread(target=loop)
    t.start()
# # for i in range(0, thread_num):
# #     t = threading.Thread(target=loop, name=f"LoopThread {i}")
# #     t.start()
# print(range(0, thread_num))
