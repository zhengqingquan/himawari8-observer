import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 软件名称
PROGRAM_NAME = "himawari8-observer"

# 软件版本
SOFTWARE_VERSION = "1.1.0"

# 日志路径
LOG_PATH="debug_log.txt"

# 程序的描述
DESCRIPTION = """
            这是参数描述
            """

# 程序参数帮助的结尾。
EPILOG = """
        这是结尾。
        github web: https://github.com/zhengqingquan/himawari8-observer
        """
