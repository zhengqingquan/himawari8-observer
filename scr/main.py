"""
main.py

主函数入口,写一些参数相关的东西。
"""

# !/usr/bin/env python

import sys
import getopt
import argparse
import time
from args import parse_args
import requests


def main():
    args = parse_args()
    print(args.equal)

    # 使用ctrl+c退出程序，抛出KeyboardInterrupt异常。
    try:
        pass
    except KeyboardInterrupt:
        print('\n👋 goodbye')
    except Exception as ex:
        print(ex)
        exit(1)


if __name__ == '__main__':
    main()
    pass
