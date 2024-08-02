import threading
from src.log.log import log_init
from src.arg.arg import arg_init
from src.timetask import stat_time_tast
from src.UI.sysTray import setup_tray_icon
from src.event.event import wait_sys

if __name__ == "__main__":
    # 初始化日志
    log_init()

    # 参数命令
    arg_init()

    # 创建一个线程来运行托盘图标
    tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
    tray_thread.start()

    # 创建并启动调度线程
    scheduler_thread = threading.Thread(target=stat_time_tast, daemon=True)
    scheduler_thread.start()

    wait_sys()  # 等待停止事件
