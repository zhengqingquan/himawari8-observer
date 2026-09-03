"""等分瓦片图模型：观测时间 + 档位 → 本地路径与下载字典。"""

from __future__ import annotations

from pathlib import Path
from time import strftime

from src.metadata.soft_config import PROGRAM_DIR_ABS_PATH
from src.resolution_grade import grade_to_grid, tile_pixel


class Pic:
    """等分瓦片图：按分辨率档位下载多张 550×550 瓦片，再合成为一张图。"""

    himawari8_base = "https://himawari8.nict.go.jp/img/D531106"
    suffix = "png"
    pic_pixel = tile_pixel()
    dl_finish_equal = False

    def __init__(self, pic_time, grade: str, *, base_dir: Path | None = None):
        """根据观测时间与分辨率档位构造图片实例。

        Args:
            pic_time: 观测时间（struct_time）。
            grade: 档位字符串，例如 ``4d`` / ``20d``。
            base_dir: 影像根目录的父路径（其下为 ``img/``）；默认程序目录。
        """
        self.base_dir = Path(base_dir) if base_dir is not None else PROGRAM_DIR_ABS_PATH
        self.grade = grade
        self.grid_size = grade_to_grid(self.grade)
        self.year = strftime("%Y", pic_time)
        self.month = strftime("%m", pic_time)
        self.day = strftime("%d", pic_time)
        self.hour = strftime("%H", pic_time)
        self.minute = strftime("%M", pic_time)
        self.seconds = strftime("%S", pic_time)

        self.tile_dirs = []
        self.tiles = {}
        self.pic_chip = self.grid_size**2
        self.pic_side = self.pic_pixel * self.grid_size

        self.folder_top = "img"
        self.compose_subdir = "complete"
        self.folder_root = (
            f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}"
        )
        self.pic_name_equal = (
            f"{self.grade}"
            f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}.{self.suffix}"
        )
        self.folder_path = self.base_dir / self.folder_top / self.folder_root / self.compose_subdir
        self.final_path_equal = self.folder_path / self.pic_name_equal
        self.build_tiles()

    def build_tiles(self) -> None:
        """构建瓦片 url → [path, status] 映射。"""
        print("正在构建url和path的映射字典。")
        location_x = 0
        location_y = 0
        arr_url = []
        arr_path = []

        while location_y < self.grid_size:
            while location_x < self.grid_size:
                pic_name = (
                    f"{self.hour}{self.minute}{self.seconds}"
                    f"_{location_x}_{location_y}.{self.suffix}"
                )
                url = (
                    f"{self.himawari8_base}/{self.grade}/{self.pic_pixel}"
                    f"/{self.year}/{self.month}/{self.day}/{pic_name}"
                )
                puzzle_path = (
                    self.base_dir
                    / self.folder_top
                    / self.folder_root
                    / self.grade
                    / str(location_y)
                )
                pic_path = puzzle_path / pic_name

                arr_url.append(url)
                self.tile_dirs.append(puzzle_path)
                arr_path.append(pic_path)
                location_x = location_x + 1
            location_x = 0
            location_y = location_y + 1

        self.tiles = dict(zip(arr_url, arr_path))
        for key, val in self.tiles.items():
            self.tiles[key] = [val, 0]
        if self.pic_chip == len(self.tiles):
            print("url和path的映射字典构建完成。")

    def download_finish(self) -> bool:
        """全部瓦片下载完成则返回 True。"""
        self.dl_finish_equal = True
        for key, val in self.tiles.items():
            if val[1] == 0:
                self.dl_finish_equal = False
        return self.dl_finish_equal
