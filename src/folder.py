"""为瓦片与合成输出创建本地目录。"""

from __future__ import annotations

import logging
import os

from src.pic.Pic import Pic


def arr_create_folder(arr) -> None:
    """按路径列表创建目录。

    Args:
        arr: 目录路径可迭代对象。
    """
    for item in arr:
        create_folder(item)


def create_folder(folder_path) -> None:
    """若路径不存在则创建目录。

    Args:
        folder_path: 目标文件夹路径。
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def cls_create_folder(pic: Pic) -> None:
    """按 Pic 实例创建瓦片子目录与合成输出目录。

    Args:
        pic: 等分瓦片图实例。
    """
    arr_create_folder(pic.arr_puzzle)
    create_folder(pic.folder_path)
    logging.info("文件夹folder构建完成。")
