"""
日志模块

日志级别：CRITICAL > ERROR > WARNING > INFO > DEBUG

参考：
https://www.cnblogs.com/xianyulouie/p/11041777.html
https://docs.python.org/zh-cn/3.7/library/logging.html
"""
import logging
import os
from head.define import LOG_PATH

# def log_init():
"""
日志模块的初始化
:return:
"""
# 创建一个logger
# 注意永远不要直接实例化Loggers，应当通过模块级别的函数logging.getLogger(name)。
# 多次使用相同的名字调用getLogger()会一直返回相同的Logger对象的引用。
logger = logging.getLogger()
# 设置logger等级开关
logger.setLevel(logging.INFO)

# 设置日志级别为NOTSET
# 表示低于WARNING等级的消息也会打印到控制台上。
# logging.basicConfig(level=logging.NOTSET)

# 创建日志文件，以些方式打开
file_handler = logging.FileHandler(LOG_PATH, mode='w')

# 设置输出到文件日志的等级开关
file_handler.setLevel(logging.DEBUG)
# fp = open(LOG_PATH, mode="w")

# 定义file_handler的输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
file_handler.setFormatter(formatter)

# 将logger添加到file_handler里面
# 也就是将本应该输出到控制台的东西也写入日志文件中
logger.addHandler(file_handler)

# logging.debug("debug")
# logger.info("info")
# logger.warning("warning")
# logger.error("error")
# logger.critical("critical")

if __name__ == '__main__':
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")
