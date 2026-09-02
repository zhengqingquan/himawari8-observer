"""
png图片的合成
"""

from PIL import Image, ImageGrab
import os
import logging
import math


def cls_photo_composition(pic):
    """
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
    screen_width, screen_height = ImageGrab.grab().size
    logging.info(f"当前屏幕分辨率: {screen_width}x{screen_height}")
    logging.info(f"当前图片分辨率: {margin}")

    expand_coefficient = 1 / 20
    logging.info(f"图片扩展系数为: {expand_coefficient}")

    expand_height = int(margin * expand_coefficient)
    logging.info(f"图片扩展宽度为: {expand_height}")

    image_coefficient = (margin + 2 * expand_height) / screen_height
    logging.info(f"屏幕分辨率扩展系数为: {image_coefficient}")

    screen_width = int(math.ceil(screen_width * image_coefficient))
    screen_height = int(math.ceil(screen_height * image_coefficient))
    logging.info(f"生成的壁纸分辨率为: {screen_width}x{screen_height}")

    image_x = int(math.ceil(screen_width / 2 - margin / 2))
    image_y = expand_height
    logging.info(f"合成时原图的坐标为: ({image_x}, {image_y})")

    joint = Image.new("RGB", (screen_width, screen_height))
    img = Image.open(file)
    joint.paste(img, image_x, image_y)
    logging.info("开始合成。")
    joint.save(path)
    logging.info(f"合成完毕：{path}")
