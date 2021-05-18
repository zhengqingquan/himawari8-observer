"""
参数解析部分
"""
import argparse
from scr.head.define import *

def parse_args():
    description = """
                这是参数描述
                wallpaper argparse cookbook
                """
    epilog = """
            这是结尾。
            github web: https://github.com/zhengqingquan/himawari8-observer
            """
    # 实例化解析器对象
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description=description,  # 程序描述
                                     add_help=True,  # 解析器默认添加一个-h/--help选项
                                     epilog=epilog
                                     )

    # 为解析器添加参数
    # 当parse_args()被调用，选项会以"-"前缀识别，剩下的参数则会被假定为位置参数
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"%(prog)s {SOFTWARE_VERSION}")

    parser.add_argument("-e",
                        "--equal",
                        type=int,
                        choices=[4, 8, 16, 20],
                        dest="equal",
                        default=20,
                        help="\"Equal\" represents how many 550-pixel images one side of an image is equal to.")
    parser.add_argument("-s",
                        "--stop",
                        default=False,
                        help="stop download.")

    # 解析器解析参数。它将检查命令行，把每个参数转换为适当的类型然后调用相应的操作。
    # args = parser.parse_args()

    # print(type(args))
    # print(args)

    # ================================================
    # parser = argparse.ArgumentParser(description='Process some integers.')
    # parser.add_argument('integers', metavar='N', type=int, nargs='+',
    #                     help='an integer for the accumulator')
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')

    args = parser.parse_args()
    # print(args.accumulate(args.integers))
    return args


if __name__ == '__main__':
    parse_args()
    pass
