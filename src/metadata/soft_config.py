import sys
from pathlib import Path

# 程序路径
PROGRAM_DIR_ABS_PATH = Path(sys.argv[0]).absolute().parent

# 日志文件的保存路径
LOG_PATH = PROGRAM_DIR_ABS_PATH.joinpath("debug_log.txt")

# 支持下载的分辨率
IMAGE_RESOLUTION = [550, 2200, 4400, 8800, 11000]

# 默认使用的分辨率
DEFAULT_RESOLUTION = 4400

# 下载图片的间隔时间（单位：秒）
DOWNLOAD_INTERVAL_TIME = 20 * 60
