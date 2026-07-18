import threading
import logging
from src.log.log import log_init
from src.arg.arg import Config
from src.main import main
from src.UI.sysTray import setup_tray_icon
from src.timetask import stat_time_tast
from src.event.event import wait_sys

if __name__ == "__main__":
    try:
        # 初始化日志
        log_init()

        # 处理参数命令和初始化程序配置
        Config()

        # 创建一个线程来运行托盘图标（注入壁纸更新入口）
        tray_thread = threading.Thread(
            target=lambda: setup_tray_icon(main), daemon=True
        )
        tray_thread.start()

        # 创建并启动调度线程（注入同一入口）
        scheduler_thread = threading.Thread(
            target=lambda: stat_time_tast(main), daemon=True
        )
        scheduler_thread.start()

        # 等待停止事件
        wait_sys()
    except Exception as e:
        logging.error(e)
