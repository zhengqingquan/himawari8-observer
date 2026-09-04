import sys
from pathlib import Path

from src.resolution_grade import default_grade, grade_to_pixel, supported_pixels

PROGRAM_DIR_ABS_PATH = Path(sys.argv[0]).absolute().parent
LOG_PATH = PROGRAM_DIR_ABS_PATH.joinpath("debug_log.txt")
IMAGE_RESOLUTION = supported_pixels()
DEFAULT_RESOLUTION = grade_to_pixel(default_grade())
DOWNLOAD_INTERVAL_TIME = 10 * 60
DEFAULT_MARGIN_TOP_PERCENT = 0.0
DEFAULT_MARGIN_BOTTOM_PERCENT = 5.0
MARGIN_PERCENT_CHOICES = (0.0, 5.0, 8.0, 10.0, 12.0, 15.0)
