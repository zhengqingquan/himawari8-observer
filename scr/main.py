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
    try:
        # 从命令行进入
        parser = arge_init()
        args, unknown = parse_args(parser)
        print("当前系统环境为：" + get_win())
        print("equal为：" + args.equal)

        # 打开下载连接
        requester = dl_init()

        # 获取时间
        time_str = get_last_time(requester)

        # exit(1)

        # 实例化图片
        main_pic = Pic(time_str, args.equal)

        # 根据时间创建文件夹folder
        cls_create_folder(main_pic)

        # 根据dic进行下载
        dl_dic_pic(main_pic, requester)
        # print_dic(main_pic.dic)

        # 合成图片
        cls_photo_composition(main_pic)

        # 替换桌面
        # pic_wallpaper(main_pic)

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


if __name__ == '__main__':
    main2()
