"""
参数解析部分
"""
import argparse
from head.define import *


def arge_init():
    """
    TODO:更多的更完整的命令
    参数解析的初始化
    :return:返回解析器parser
    """
    # 实例化解析器对象
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,  # 程序名
                                     description=DESCRIPTION,  # 参数描述
                                     epilog=EPILOG,  # 结尾描述
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
                        dest="equal",
                        default="1d",
                        help="\"Equal\" represents how many 550-pixel images one side of an image is equal to.")

    parser.add_argument("-s",
                        "--stop",
                        default=False,
                        help="stop download.")
    parser.add_argument("-b",
                        "--begin",
                        default=True,
                        help="begin download.")
    return parser


def parse_args(parser):
    # 解析器解析参数。它将检查命令行，把每个参数转换为适当的类型然后调用相应的操作。
    # try:
    #     # args = parser.parse_args()
    #     args, unknown = parser.parse_known_args()
    #     return args
    # # args, unknown = parser.parse_args()
    # except SystemExit:
    #     pass
    # args, unknown = parser.parse_known_args()  # 当输入正确参数时候正常运行。当输入错误参数时不退出，未知参数被存入unknown
    # args = parser.parse_args() # 当输入正确参数时正常运行。当输入错误参数时候触发SystemExit异常。并输出错误参数的内容。
    # args = parser.parse_known_args()  # 当输入如-h会触发SystemExit异常。
    # print(args)
    # print(unknown)

    try:
        # args = parser.parse_args() # 多个命令时会报错
        # args, unknown = parser.parse_args()
        # args = parser.parse_known_args()
        args, unknown = parser.parse_known_args()  # 多个命令时，不会报错
        print(f"当前输入参数：{args}")
        print(f"当前未知参数：{unknown}")
        return args, unknown
    except SystemExit:
        pass
    return None, None


if __name__ == '__main__':
    parse_args()
    pass
