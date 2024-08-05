import threading
import logging
from src.log.log import log_init
from src.arg.arg import Config
from src.timetask import stat_time_tast
from src.UI.sysTray import setup_tray_icon
from src.event.event import wait_sys

if __name__ == "__main__":
    try:
        # 初始化日志
        log_init()

        # 处理参数命令和初始化程序配置
        Config()

        # # 创建一个线程来运行托盘图标
        tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
        tray_thread.start()

        # 创建并启动调度线程
        # scheduler_thread = threading.Thread(target=stat_time_tast, daemon=True)
        # scheduler_thread.start()

        wait_sys()  # 等待停止事件
    except Exception as e:
        logging.error(e)