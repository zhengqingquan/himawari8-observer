"""
png图片的合成
"""
from PIL import Image, ImageGrab
import os
import logging
import math


def photo_composition2(array_pic, equal, save_path):
    """
    把照片的路径存在一个数组中，根据像素合成照片。在保存到路径。
    :param array_pic:存储照片的数组
    :param equal:照片的像素（分为多少份）
    :param save_path:合成的图片保存的路径
    :return:
    """
    # 初始化一张底片。
    joint = Image.new("RGB", (11000, 11000))
    axis_x = 0
    axis_y = 0
    while axis_y < 20:
        while axis_x < 20:
            subscript = (axis_x + 1) * (axis_y + 1) - 1
            print(f"当前正在合成第{subscript}个：{axis_x}_{axis_y}")
            img = Image.open(array_pic[subscript])
            print("x轴的位置：" + str(550 * axis_x))
            print("y轴的位置：" + str(550 * axis_y))
            joint.paste(img, (550 * axis_x, 550 * axis_y))  # (x，y)
            axis_x = axis_x + 1
        axis_x = 0
        axis_y = axis_y + 1

    # i = 0
    # while i < 19:
    #     print("当前正在合成：" + array_pic[i])
    #     img = Image.open(array_pic[i])
    #     print("x轴的位置：" + str(550 * i))
    #     joint.paste(img, (550 * i, 0))  # (x，y)
    #     i = i + 1

    # 保存图片
    joint.save(save_path)
    '''
    img2 = Image.open("try2.png")
    size2 = img2.size  # (550,550)
    print(type(size2))
    print(size2)
    print(size2[0])

    joint = Image.new("RGB", (1100, 550))  # （长，宽）
    joint.paste(img2, (0, 0))  # 图片从哪开始（x，y）
    joint.save('horizontal2.png')
    '''

    # img = Image.open("try4.png")
    # size = img.size
    # joint = Image.new("RGB", (1100, 550))
    # joint.paste(img, (255, 0))  # (x，y)
    # joint.save('horizontal2.png')


def photo_composition(array_pic, equal, save_path):
    """
    把照片的路径存在一个数组中，根据像素合成照片。在保存到路径。
    :param array_pic:存储照片的数组
    :param equal:照片的像素（分为多少份）
    :param save_path:合成的图片保存的路径
    :return:
    """
    # 初始化一张底片。
    joint = Image.new("RGB", (11000, 11000))
    axis_x = 0
    axis_y = 0
    while axis_y < 20:
        while axis_x < 20:
            subscript = axis_y * 20 + axis_x + 1
            print(f"当前正在合成第{subscript}个：{axis_x}_{axis_y}")
            img = Image.open(array_pic[subscript - 1])
            print(array_pic[subscript - 1])
            print("x轴的位置：" + str(550 * axis_x))
            print("y轴的位置：" + str(550 * axis_y))
            joint.paste(img, (550 * axis_x, 550 * axis_y))  # (x，y)
            axis_x = axis_x + 1
        axis_x = 0
        axis_y = axis_y + 1
    joint.save(save_path)


def cls_photo_composition(pic):
    """
    Finish
    将多张碎片照片合成一张完整的照片。
    :param pic:Pic类，表示某张照片。
    :return:
    """
    axis_x = 0
    axis_y = 0
    joint = Image.new("RGB", (pic.pic_side, pic.pic_side))
    for key, val in pic.dic.items():
        img = Image.open(val[0])
        joint.paste(img, (pic.pic_pixel * axis_x, pic.pic_pixel * axis_y))  # (x，y)
        axis_x += 1
        if axis_x >= pic.int_equal:
            axis_x = 0
            axis_y += 1
    joint.save(pic.final_path_equal)
    print(f"图片合成结束。路径为：{os.path.abspath(pic.final_path_equal)}")


def fix_pic(file, margin, path):
    """
    将图片从11000*11000像素，变成12100*12100像素。为了美观，用于增加黑边，不会被任务栏遮挡。
    :param file:原文件路径。
    :param margin:边缘的宽度，如果是要变成12100，则该值为550，单位为：像素。
    :param path:保存后的文件路径。
    :return:None
    """
    # 获取屏幕分辨率
    screen_width, screen_height = ImageGrab.grab().size
    logging.info(f"当前屏幕分辨率: {screen_width}x{screen_height}")
    logging.info(f"当前图片分辨率: {margin}")

    expand_coefficient = 1/20
    logging.info(f"图片扩展系数为: {expand_coefficient}")

    expand_height = int(margin * expand_coefficient)
    logging.info(f"图片扩展宽度为: {expand_height}")

    image_coefficient = (margin + 2 * expand_height) / screen_height
    logging.info(f"屏幕分辨率扩展系数为: {image_coefficient}")

    screen_width = int(math.ceil(screen_width * image_coefficient))
    screen_height = int(math.ceil(screen_height * image_coefficient))
    logging.info(f"生成的壁纸分辨率为: {screen_width}x{screen_height}")

    image_x = int(math.ceil(screen_width/2 - margin/2))
    image_y = expand_height
    logging.info(f"合成时原图的坐标为: ({image_x}, {image_y})")

    joint = Image.new("RGB", (screen_width, screen_height))
    img = Image.open(file)
    joint.paste(img, image_x, image_y)
    logging.info("开始合成。")
    joint.save(path)
    logging.info(f"合成完毕：{path}")

def png_to_jpg(path):
    quality = 95  # 将pngz图片质量，1~95（1最差，95最高），默认75。
    # path = 'C:/Users/96400/Downloads/154000_0_0.png'
    img = Image.open(path)
    new_img = Image.new("RGB", img.size)
    new_img.paste(img, (0, 0))
    new_img.convert('RGB').save(r'G:\work\himawari8-observer\img\20240723031000\complete\8d20240723031000.jpg', "JPEG", quality=quality)


if __name__ == "__main__":
    # arr_pic = []
    # temp_X = 0
    # temp_Y = 0
    # while temp_Y < 20:
    #     while temp_X < 20:
    #         arr_pic.append(f"../img/20210515052000/puzzle/{temp_Y}/052000_{temp_X}_{temp_Y}.png")
    #         # print(f"../img/20210515052000/puzzle/{temp_Y}/052000_{temp_X}_{temp_Y}.png")
    #         temp_X = temp_X + 1
    #     temp_X = 0
    #     temp_Y = temp_Y + 1
    # # print(len(arr_pic))
    # photo_composition(array_pic=arr_pic, save_path="../img/20210515052000/complete/temp1.png", equal="")

    # fix_pic("../img/20210515052000/complete/temp1.png", 550, "../img/20210515052000/complete/fix_temp1.png")
    # png_to_jpg(r'G:\work\himawari8-observer\img\20240723031000\complete\8d20240723031000.png')

    # 创建一个日志记录器对象 logger。未使用参数，默认为根记录器。
    logger = logging.getLogger()
    # 设置 logger 的日志等级。
    logger.setLevel(logging.DEBUG)

    # fix_pic("src/picdeal/4d20240802090000.png",2200,"src/picdeal/4d202408020900002.png")
