"""
日志模块
"""

import logging
from src.metadata.soft_config import LOG_PATH

def log_init():
    """
    日志模块的初始化。
    :return:
    """

    # 创建一个日志记录器对象 logger。未使用参数，默认为根记录器。
    logger = logging.getLogger()
    # 设置 logger 的日志等级。
    logger.setLevel(logging.DEBUG)

    # 创建一个流（控制台）处理器。
    console_handler = logging.StreamHandler()
    # 设置输出到控制台的等级。
    console_handler.setLevel(logging.INFO)
    # 定义输出到控制台的格式。
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    # 将控制台处理器添加到日志记录器中。
    logger.addHandler(console_handler)

    # 创建文件处理器（默认为追加模式）。
    logging.info(f"Log path：{LOG_PATH}")
    file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
    # 设置输出到文件日志的等级。
    file_handler.setLevel(logging.DEBUG)
    # 定义输出到文件日志的格式。
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
    # 将文件处理器添加到日志记录器中。
    logger.addHandler(file_handler)
