"""壁纸更新流水线：编排观测时间→瓦片→等分合成图→可选修边→设桌面→可选清理。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from time import struct_time

from src.cls.Pic import Pic
from src.dl.dlinit import dl_init, get_last_time
from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
    PROGRAM_DIR_ABS_PATH,
)
from src.picdeal.photofunia import cls_photo_composition, fix_pic
from src.resolution_grade import default_grade
from src.tile_download import download_tiles
from src.tool.cleanup import cleanup_after_wallpaper_apply
from src.tool.folder import cls_create_folder
from src.tool.wallpaper import path_wallpaper

FetchObservationTime = Callable[[], struct_time]
DownloadTiles = Callable[[Pic], None]
ComposeEqual = Callable[[Pic], None]
AdjustWallpaper = Callable[[Pic], Path]
SetWallpaper = Callable[[Path], bool | None]


def _default_fetch_observation_time() -> struct_time:
    return get_last_time(dl_init())


def _default_download_tiles(pic: Pic) -> None:
    download_tiles(pic)


def _default_compose_equal(pic: Pic) -> None:
    cls_photo_composition(pic)


def _default_set_wallpaper(path: Path) -> bool | None:
    return path_wallpaper(path)


def run_wallpaper_pipeline(
    *,
    fetch_observation_time: FetchObservationTime | None = None,
    download_tiles: DownloadTiles | None = None,
    compose_equal: ComposeEqual | None = None,
    adjust_wallpaper: AdjustWallpaper | None = None,
    set_wallpaper: SetWallpaper | None = None,
    resolution_grade: str | None = None,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    cleanup_after_apply: bool = True,
) -> None:
    """跑一次壁纸更新。副作用步骤可注入，便于测试。"""
    fetch = fetch_observation_time or _default_fetch_observation_time
    download = download_tiles or _default_download_tiles
    compose = compose_equal or _default_compose_equal
    set_desktop = set_wallpaper or _default_set_wallpaper
    grade = resolution_grade if resolution_grade is not None else default_grade()

    def default_adjust(pic: Pic) -> Path:
        src = Path(pic.final_path_equal)
        out = src.with_name(f"{src.stem}_adjust{src.suffix}")
        fix_pic(
            str(src),
            pic.pic_side,
            str(out),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
        )
        return out

    adjust = adjust_wallpaper or default_adjust

    time_str = fetch()
    pic = Pic(time_str, grade)
    cls_create_folder(pic)
    download(pic)
    if not pic.download_finish():
        logging.warning("瓦片未全部下载完成，跳过合成与设壁纸")
        return
    compose(pic)
    wallpaper_path = adjust(pic) if auto_adjust else Path(pic.final_path_equal)
    applied = set_desktop(wallpaper_path)
    if cleanup_after_apply and applied is not False:
        current_run_root = Path(pic.folder_path).parent
        cleanup_after_wallpaper_apply(
            img_root=PROGRAM_DIR_ABS_PATH / pic.folder_top,
            current_run_root=current_run_root,
            keep_file=Path(wallpaper_path),
        )
