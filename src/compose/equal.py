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


def fix_pic(file, margin, path, *, top_percent=5.0, bottom_percent=5.0):
    """
    将正方形等分合成图嵌入与屏幕同比例的黑边画布。

    :param file: 原文件路径
    :param margin: 原图边长（像素）
    :param path: 保存路径
    :param top_percent: 顶边黑边占原图边长的百分比
    :param bottom_percent: 底边黑边占原图边长的百分比
    """
    screen_width, screen_height = ImageGrab.grab().size
    logging.info(f"当前屏幕分辨率: {screen_width}x{screen_height}")
    logging.info(f"当前图片边长: {margin}")
    logging.info(f"修边百分比: top={top_percent}% bottom={bottom_percent}%")

    top_expand = int(margin * top_percent / 100.0)
    bottom_expand = int(margin * bottom_percent / 100.0)
    content_height = margin + top_expand + bottom_expand

    scale = content_height / screen_height
    canvas_width = int(math.ceil(screen_width * scale))
    canvas_height = content_height
    logging.info(f"生成的壁纸分辨率为: {canvas_width}x{canvas_height}")

    image_x = int(math.ceil((canvas_width - margin) / 2))
    image_y = top_expand
    logging.info(f"合成时原图的坐标为: ({image_x}, {image_y})")

    joint = Image.new("RGB", (canvas_width, canvas_height), color=(0, 0, 0))
    with Image.open(file) as img:
        joint.paste(img, (image_x, image_y))
    logging.info("开始合成。")
    joint.save(path)
    logging.info(f"合成完毕：{path}")
