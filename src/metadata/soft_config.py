import sys
from pathlib import Path

from src.resolution_grade import default_grade, grade_to_pixel, supported_pixels

# 程序路径
PROGRAM_DIR_ABS_PATH = Path(sys.argv[0]).absolute().parent

# 日志文件的保存路径
LOG_PATH = PROGRAM_DIR_ABS_PATH.joinpath("debug_log.txt")

# 支持下载的分辨率（像素边长；映射见 resolution_grade）
IMAGE_RESOLUTION = supported_pixels()

# 默认使用的分辨率（与真路径默认档位一致）
DEFAULT_RESOLUTION = grade_to_pixel(default_grade())

# 下载图片的间隔时间（单位：秒）
DOWNLOAD_INTERVAL_TIME = 20 * 60

# 修边黑边占原图边长的默认百分比
DEFAULT_MARGIN_TOP_PERCENT = 5.0
DEFAULT_MARGIN_BOTTOM_PERCENT = 5.0

# 托盘可选的黑边百分比预设
MARGIN_PERCENT_CHOICES = (0.0, 5.0, 8.0, 10.0, 12.0, 15.0)
