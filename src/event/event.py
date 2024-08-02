import threading

# 使用事件保持主线程运行
stop_event = threading.Event()

def end_main_sys():
    stop_event.set()  # 触发停止事件

def wait_sys():
    stop_event.wait()  # 等待停止事件