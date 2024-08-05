"""
参数解析部分
"""

import argparse
from src.metadata.soft_info import *

def arge_init():
    """
    TODO:更多的更完整的命令
    参数解析的初始化
    参考：
        https://blog.csdn.net/MOU_IT/article/details/81782386
        https://www.cnblogs.com/cheyunhua/p/11002421.html
    :return:返回解析器parser
    """
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

    parser.add_argument("-o",
                        "--out",
                        default=True,  # 默认为True，表示程序不会自动退出
                        dest="out_state",
                        action="store_false",  # 当输入-o时，变成False，程序将退出
                        help="out program")

    parser.add_argument("-m",
                        "--modify",
                        default=True,
                        action="store_false",  # 默认为False，当输入-e时，变成True
                        help="modify picture, become 12100*12100 pixel")

    parser.add_argument("-dl",
                        "--download",
                        type=str,
                        choices=["complete", "equal"],
                        default="equal",
                        const="equal",
                        dest="dl_way",
                        action="store",
                        nargs="?",
                        help="download way and begin.")
    # parser.error("")  # 用来自定义错误信息。
    return parser


def parse_args(parser, in_args=None):
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
        args, unknown = parser.parse_known_args(args=in_args)  # 多个命令时，不会报错
        print(f"当前输入参数：{args}")
        print(f"当前未知参数：{unknown}")
        return args, unknown
    except SystemExit:
        print("捕获到错误")
        pass
    return None, None


if __name__ == '__main__':
    parse_args()
    pass
