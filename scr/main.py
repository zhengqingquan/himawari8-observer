"""
main.py

主函数入口,写一些参数相关的东西。
"""

# !/usr/bin/env python

import sys
import getopt
import argparse


def main():
    description = """
                这是参数描述
                wallpaper argparse cookbook
                """

    # 实例化解析器对象
    parser = argparse.ArgumentParser(description=description,  # 程序描述
                                     add_help=False  # 为解析器默认不添加应该-h/--help选项
                                     )

    # 为解析器添加参数
    # 当parse_args()被调用，选项会以"-"前缀识别，剩下的参数则会被假定为位置参数
    parser.add_argument("-h", "help")
    # parser.add_argument("-h", dest="--help", help="some help")
    # parser.add_argument('-v', dest='--version', help="get version")
    # parser.add_argument('integers', metavar='N', type=int, nargs='+',
    #                     help='an integer for the accumulator')

    # 解析器解析参数。它将检查命令行，把每个参数转换为适当的类型然后调用相应的操作。
    args = parser.parse_args([])

    # 打印参数值
    # print(f"User input code version is:{args.version}")
    # print(args.accumulate(args.integers))


if __name__ == '__main__':
    main()
