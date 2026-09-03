from __future__ import annotations

from pathlib import Path
from time import strftime

from src.metadata.soft_config import PROGRAM_DIR_ABS_PATH
from src.resolution_grade import grade_to_grid, tile_pixel


class Pic(object):
    """等分瓦片图：按分辨率档位下载多张 550×550 瓦片，再合成为一张图。"""

    himawari8_base = "https://himawari8.nict.go.jp/img/D531106"
    suffix = "png"
    pic_pixel = tile_pixel()
    dl_finish_equal = False

    def __init__(self, pic_time, equal, *, base_dir: Path | None = None):
        """
        根据观测时间与分辨率档位构造图片实例。
        :param pic_time: 观测时间
        :param equal: 档位字符串，例如 20d
        :param base_dir: 影像根目录的父路径（其下为 img/）；默认程序目录
        """
        self.base_dir = Path(base_dir) if base_dir is not None else PROGRAM_DIR_ABS_PATH
        self.str_equal = equal
        self.int_equal = grade_to_grid(self.str_equal)
        self.year = strftime("%Y", pic_time)
        self.month = strftime("%m", pic_time)
        self.day = strftime("%d", pic_time)
        self.hour = strftime("%H", pic_time)
        self.minute = strftime("%M", pic_time)
        self.seconds = strftime("%S", pic_time)

        self.arr_puzzle = []
        self.dic = {}
        self.pic_chip = self.int_equal**2
        self.pic_side = self.pic_pixel * self.int_equal

        self.folder_top = "img"
        # 合成输出子目录名（历史命名，与已废弃的 complete 下载无关）
        self.folder_complete = "complete"
        self.folder_root = (
            f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}"
        )
        self.pic_name_equal = (
            f"{self.str_equal}"
            f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}.{self.suffix}"
        )
        self.folder_path = (
            self.base_dir / self.folder_top / self.folder_root / self.folder_complete
        )
        self.final_path_equal = self.folder_path / self.pic_name_equal
        self.build_dic()

    def build_dic(self):
        """构建瓦片 url → [path, status] 映射。"""
        print("正在构建url和path的映射字典。")
        location_x = 0
        location_y = 0
        arr_url = []
        arr_path = []

        while location_y < self.int_equal:
            while location_x < self.int_equal:
                pic_name = (
                    f"{self.hour}{self.minute}{self.seconds}"
                    f"_{location_x}_{location_y}.{self.suffix}"
                )
                url = (
                    f"{self.himawari8_base}/{self.str_equal}/{self.pic_pixel}"
                    f"/{self.year}/{self.month}/{self.day}/{pic_name}"
                )
                puzzle_path = (
                    self.base_dir
                    / self.folder_top
                    / self.folder_root
                    / self.str_equal
                    / str(location_y)
                )
                pic_path = puzzle_path / pic_name

                arr_url.append(url)
                self.arr_puzzle.append(puzzle_path)
                arr_path.append(pic_path)
                location_x = location_x + 1
            location_x = 0
            location_y = location_y + 1

        self.dic = dict(zip(arr_url, arr_path))
        for key, val in self.dic.items():
            self.dic[key] = [val, 0]
        if self.pic_chip == len(self.dic):
            print("url和path的映射字典构建完成。")

    def download_finish(self):
        """全部瓦片下载完成则返回 True。"""
        self.dl_finish_equal = True
        for key, val in self.dic.items():
            if val[1] == 0:
                self.dl_finish_equal = False
        return self.dl_finish_equal
