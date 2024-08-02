import argparse
import logging
from src.head.define import *
from src.head.config import *

class Config:
    _instance = None
    _parser = None
    _args = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.parse_arguments()
        self._initialized = True

    def parse_arguments(self):
        # 实例化解析器对象
        self._parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                        description=DESCRIPTION,
                                        epilog=EPILOG,
                                        # usage=argparse.SUPPRESS,  # 关闭用例usage，该值默认为None
                                        # add_help=True  # 为解析器默认添加一个-h/--help选项
                                        )

        # 为解析器添加参数
        # 当parse_args()被调用，选项会以"-"前缀识别，剩下的参数则会被假定为位置参数
        self._parser.add_argument("-dl",
                            "--download",
                            type=str,
                            choices=["complete", "equal"],
                            default="equal",
                            const="equal",
                            dest="download_method",
                            action="store",
                            nargs="?",
                            help="download way and begin.")

        self._parser.add_argument("-r",
                            "--resolution",
                            choices=IMAGE_RESOLUTION,
                            default=DEFAULT_RESOLUTION,
                            const=DEFAULT_RESOLUTION,
                            action="store",
                            dest="download_resolution",
                            nargs="?",
                            help="\"Equal\" represents how many 550-pixel images one side of an image is equal to.")

        self._parser.add_argument("-a",
                            "--adjust",
                            dest="is_auto_adjust_picture",
                            default=False,
                            action="store_false",
                            help="Automatically adjust images. Prevent being obscured by the taskbar.")

        self._parser.add_argument("-v",
                            "--version",
                            action="version",
                            version=f"%(prog)s {SOFTWARE_VERSION}")

        # Check if there are no arguments
        # if len(sys.argv) <= 1:
        #     self._parser.print_help()
        #     sys.exit(1)

        # 解析参数。
        self._args = self._parser.parse_args()

        logging.info(f"Download method: {self._args.download_method}")
        logging.info(f"Download resolution: {self._args.download_resolution}")
        logging.info(f"Is auto adjust picture: {self._args.is_auto_adjust_picture}")

    # TODO 可以重新解析参数。
    def parse_known_args(self, args):
        self._parser.parse_known_args(args)

    def get_download_method(self):
        return self._args.download_method

    def get_download_resolution(self):
        return self._args.download_resolution

    def is_auto_adjust_picture(self):
        return self._args.is_auto_adjust_picture
