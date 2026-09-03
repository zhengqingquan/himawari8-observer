"""为瓦片与合成输出创建本地目录。"""

from __future__ import annotations

import logging
import os

from src.pic.pic import Pic


def create_folders(paths) -> None:
    """按路径列表创建目录。

    Args:
        paths: 目录路径可迭代对象。
    """
    for item in paths:
        create_folder(item)


def create_folder(folder_path) -> None:
    """若路径不存在则创建目录。

    Args:
        folder_path: 目标文件夹路径。
    """
    if os.path.exists(folder_path):
        return
    try:
        os.makedirs(folder_path)
    except OSError:
        logging.exception("Failed to create folder: %s", folder_path)
        raise


def create_pic_folders(pic: Pic) -> None:
    """按 Pic 实例创建瓦片子目录与合成输出目录。

    Args:
        pic: 等分瓦片图实例。
    """
    create_folders(pic.tile_dirs)
    create_folder(pic.folder_path)
    logging.info(
        "Created tile and compose folders for grade %s under %s",
        pic.grade,
        pic.base_dir / pic.folder_top / pic.folder_root,
    )
