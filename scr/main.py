"""
main.py

主函数入口,写一些参数相关的东西。
"""

# !/usr/bin/env python

from args import *
from dl.dlpic import *
from dl.dlinit import *
from tool.tool import *
from picdeal.photofunia import *
from cls.Pic import *
from tool.wallpaper import *
from log.log import *
import sys


def main():
    parser = arge_init()
    args, unknown = parse_args(parser)
    print(sys.argv)
    print(args)
    print(unknown)
    print("当前系统环境为：" + get_win())
    exit(1)

    parser = arge_init()
    while True:
        try:
            # 从命令行进入
            args, unknown = parse_args(parser)
            print("当前系统环境为：" + get_win())
            print("equal为：" + args.equal)

            # 打开下载连接
            requester = dl_init()

            # 获取时间
            time_str = get_last_time(requester)

            # 根据时间创建文件夹folder
            # create_dic_folder(time_str)

            # 把时间转换成url的数组
            # arr_url = time_to_url(time_str)
            # print_arr(arr_url)

            # 把时间转换成存储路径path的数组
            # arr_path = time_to_path(time_str)
            # print_arr(arr_path)

            # 创建url和path的映射字典dic
            # dic_dl = dic_url_path(arr_url, arr_path)
            # print_dic(dic_dl)

            # 根据dic进行下载
            # dl_dic_pic(dic_dl, requester)

            # 合成图片
            # photo_composition(array_pic=arr_path, equal="", save_path="../img/20210515052000/complete/temp1.png")

            # 替换桌面

        except Exception as e:  # e代表error，可以用来访问异常中的一些关键字。
            print(e.__class__.__name__)
            print(e)

        # except AttributeError:
        #     print("AttributeError")
        #     pass
        except KeyError:
            print("KeyError")

        # 使用ctrl+c退出程序，抛出KeyboardInterrupt异常。
        except KeyboardInterrupt:
            print('\n👋 goodbye')


def main2():
    """
    用户命令行交互主程序。
    :return:None
    """
    # 从命令行进入。相当于初始化程序
    parser = arge_init()  # 参数解析器的初始化
    in_args = sys.argv[1:]  # 初始化用户首次输入的指令

    # 让用户不退出程序
    # 参考：https://segmentfault.com/q/1010000014367478
    while True:
        try:
            print("当前系统环境为：" + get_win())
            print(f"himawari8-observer版本为：{SOFTWARE_VERSION}")
            # 解析用户输入
            args, unknown = parser.parse_known_args(args=in_args)  # parse_known_args()方法在多个命令时，不会报错
            print(f"当前输入参数：{args}")
            print(f"当前未知参数：{unknown}")

            # 程序的运行
            program(args)

            # 让用户重新输入新的指令
            print("\n可以使用ctrl+C来退出程序")
            in_args = input('>>>').split()
            if len(in_args) is 0:
                in_args.append("-h")

            # 重新解析用户的输入
            args, unknown = parser.parse_known_args(args=in_args)
            print(f"当前输入参数：{args}")
            print(f"当前未知参数：{unknown}")

            # 若输入了-o参数则退出程序
            if args.out_state is False:
                break

        except SystemExit:
            try:
                print("触发SystemExit错误。")

                # 触发参数异常后让用户重新输入。
                in_args = input('>>>').split()
                if len(in_args) is 0:
                    in_args.append("-h")

            # 在SystemExit异常中也需要进行KeyboardInterrupt的异常处理。
            except KeyboardInterrupt:  # 需要放到Terminal才能触发。
                print('👋 goodbye')
                break

        except KeyboardInterrupt:  # 需要放到Terminal才能触发。
            print('👋 goodbye')
            break

    print("程序退出。")
    exit(1)

    # while args.out_state:
    #     if args.out_state is False:
    #         exit(1)
    #     cmd = input('>>>').split()  # 让用户输入
    #     args, unknown = parse_args(parser, cmd)  # 参数的解析
    #     print("equal为：" + args.equal)
    #     try:
    #         print("下载方式为：" + args.dl_way)
    #         print("当前系统环境为：" + get_win())
    # except Exception as e:  # e代表error，可以用来访问异常中的一些关键字。
    #     print(e.__class__.__name__)
    #     print(e)


def program(args):
    """
    功能运行主程序。根据传入的args执行程序。
    :param args:命令行传入的参数。
    :return:None
    """
    # 打开下载连接
    requester = dl_init()

    # 获取最新的时间
    time_str = get_last_time(requester)

    # 实例化图片pic类
    main_pic = Pic(time_str, args.equal)
    print(main_pic.post_data)
    print(main_pic.final_path_cpl)

    # 根据时间创建文件夹folder
    cls_create_folder(main_pic)
    print(type(args.dl_way))
    # 默认使用post
    if args.dl_way == "equal": # 字符串的比对需要使用==而不是is，因为字符串是地址的比对，而我们需要的是内容的比对。
        # 根据dic进行下载
        dl_dic_pic(main_pic, requester)
        print_dic(main_pic.dic)

        # 合成图片
        cls_photo_composition(main_pic)
    else:
        dl_post_pic(main_pic, requester)

    # 如果是win7版本，需要修改为jpg格式。
    # png_to_jpg()

    # 修正一下图片，让其更好看一些。
    # fix_pic()

    # 替换桌面
    # pic_wallpaper(main_pic)


if __name__ == '__main__':
    main2()
