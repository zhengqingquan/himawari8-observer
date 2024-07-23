"""
更换window桌面
"""

import os
import ctypes
from pathlib import Path

def pic_wallpaper(pic):
    """
    根据传入的图片替换桌面背景。
    :param pic:类pic
    :return:1 or 0
    """
    return path_wallpaper(os.path.abspath(pic.final_path))

def path_wallpaper(wallpaper_path: Path):
    """
    根据路径替换桌面背景，win7 可能不支持 png 格式。
    :param wallpaper_path: 图片的路径。
    :return:True or False
    """
    try:
        if wallpaper_path.exists() is False:
            raise FileNotFoundError

        logging.info(f'图片路径为：{wallpaper_path.resolve()}')

        # 必须使用图片的绝对路径。若不是绝对路径，则会设置为默认的纯（黑）色背景。
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 1
        SPIF_SENDCHANGE = 2
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, os.path.abspath(wallpaper_path), 0)

        logging.info(f'图片替换完成。')

        return True
    except FileNotFoundError:
        logging.warning(f'图片不存在：{wallpaper_path}')
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f'当前工作路径：{Path.cwd()}')
    path_wallpaper(Path(r'./tool/8d20240723031000.png'))
