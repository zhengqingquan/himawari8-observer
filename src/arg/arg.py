import sys
import argparse
from src.head.define import PROGRAM_NAME, DESCRIPTION, EPILOG, SOFTWARE_VERSION

def arg_init():
    # 实例化解析器对象
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,  # 程序名
                                     description=DESCRIPTION,  # 参数描述
                                     epilog=EPILOG,  # 结尾描述
                                     usage=argparse.SUPPRESS,  # 关闭用例usage，该值默认为None
                                     add_help=True  # 为解析器默认添加一个-h/--help选项
                                    )

    # 为解析器添加参数
    # 当parse_args()被调用，选项会以"-"前缀识别，剩下的参数则会被假定为位置参数
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"%(prog)s {SOFTWARE_VERSION}")

    parser.add_argument("-e",
                    "--equal",
                    type=str,
                    choices=["1d", "4d", "8d", "16d", "20d"],
                    default="8d",
                    const="8d",
                    action="store",
                    dest="equal",
                    nargs="?",
                    help="\"Equal\" represents how many 550-pixel images one side of an image is equal to.")

    # Check if there are no arguments
    # if len(sys.argv) <= 1:
    #     parser.print_help()
    #     sys.exit(1)

    # args = parser.parse_args()