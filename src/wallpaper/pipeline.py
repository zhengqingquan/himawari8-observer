"""壁纸更新流水线：编排观测时间→瓦片→等分合成图→可选修边→设桌面→可选清理。"""

from __future__ import annotations

import logging
from collections.abc import Callable, MutableMapping
from pathlib import Path
from time import strftime, struct_time
from typing import Any

from src.cleanup import cleanup_after_wallpaper_apply
from src.compose.equal import apply_margins, compose_equal_image, compose_equal_image_with_margins
from src.download.observation import create_session
from src.download.observation import fetch_observation_time as fetch_latest_observation_time
from src.download.tiles import download_tiles
from src.folder import create_pic_folders
from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)
from src.pic.pic import Pic
from src.resolution_grade import default_grade
from src.set_wallpaper import get_desktop_wallpaper as read_desktop_wallpaper
from src.set_wallpaper import set_wallpaper as apply_desktop_wallpaper
from src.set_wallpaper import wallpaper_paths_match

FetchObservationTime = Callable[[], struct_time]
DownloadTiles = Callable[[Pic], None]
ComposeEqual = Callable[[Pic], None]
AdjustWallpaper = Callable[[Pic], Path]
SetWallpaper = Callable[[Path], bool | None]
GetDesktopWallpaper = Callable[[], str | None]
AppliedRunState = MutableMapping[str, Any]


def _default_fetch_observation_time() -> struct_time:
    return fetch_latest_observation_time(create_session())


def _default_download_tiles(pic: Pic) -> None:
    download_tiles(pic)


def _default_compose_equal(pic: Pic) -> None:
    compose_equal_image(pic)


def _default_set_wallpaper(path: Path) -> bool | None:
    return apply_desktop_wallpaper(path)


def _adjusted_output_path(pic: Pic) -> Path:
    src = Path(pic.final_path_equal)
    return src.with_name(f"{src.stem}_adjust{src.suffix}")


def build_applied_run_key(
    observation_time: struct_time,
    *,
    resolution_grade: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
) -> tuple[str, str, bool, float, float]:
    """用于判断是否可跳过重复下载的指纹（观测时间 + 影响成图的参数）。"""
    return (
        strftime("%Y-%m-%d %H:%M:%S", observation_time),
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
    )


def _remember_applied(
    applied_run_state: AppliedRunState | None,
    *,
    run_key: tuple[str, str, bool, float, float],
    wallpaper_path: Path,
    record_run_key: bool,
) -> None:
    if applied_run_state is None:
        return
    if record_run_key:
        applied_run_state["last"] = run_key
    try:
        applied_run_state["wallpaper_path"] = str(wallpaper_path.resolve())
    except OSError:
        applied_run_state["wallpaper_path"] = str(wallpaper_path)


def run_wallpaper_pipeline(
    *,
    fetch_observation_time: FetchObservationTime | None = None,
    download_tiles: DownloadTiles | None = None,
    compose_equal: ComposeEqual | None = None,
    adjust_wallpaper: AdjustWallpaper | None = None,
    set_wallpaper: SetWallpaper | None = None,
    get_desktop_wallpaper: GetDesktopWallpaper | None = None,
    resolution_grade: str | None = None,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    cleanup_after_apply: bool = True,
    base_dir: Path | None = None,
    applied_run_state: AppliedRunState | None = None,
    record_run_key: bool = True,
) -> None:
    """跑一次壁纸更新。副作用步骤可注入，便于测试。

    托盘 / 定时器只应通过 WallpaperJobRef 触发，不要直接 import 本模块或 download/。

    跳过策略（需 ``applied_run_state``）：
    - 指纹相同且桌面仍是上次壁纸文件 → 整段跳过；
    - 指纹相同但桌面已换、成品仍在 → 仅重设壁纸；
    - 否则走完整流水线。
    """
    fetch = fetch_observation_time or _default_fetch_observation_time
    download = download_tiles or _default_download_tiles
    compose = compose_equal or _default_compose_equal
    set_desktop = set_wallpaper or _default_set_wallpaper
    read_desktop = get_desktop_wallpaper or read_desktop_wallpaper
    grade = resolution_grade if resolution_grade is not None else default_grade()
    use_direct_margin_compose = auto_adjust and compose_equal is None and adjust_wallpaper is None

    def default_adjust(pic: Pic) -> Path:
        out = _adjusted_output_path(pic)
        apply_margins(
            str(pic.final_path_equal),
            pic.pic_side,
            str(out),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
        )
        return out

    adjust = adjust_wallpaper or default_adjust

    time_str = fetch()
    run_key = build_applied_run_key(
        time_str,
        resolution_grade=grade,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
    )
    if applied_run_state is not None and applied_run_state.get("last") == run_key:
        last_path_raw = applied_run_state.get("wallpaper_path")
        last_path = Path(last_path_raw) if last_path_raw else None
        if last_path is not None and last_path.is_file():
            current_desktop = read_desktop()
            if wallpaper_paths_match(current_desktop, last_path):
                logging.info(
                    "Observation params unchanged and desktop wallpaper still ours; skipping update"
                )
                return
            logging.info(
                "Observation params unchanged but desktop wallpaper differs; re-applying %s",
                last_path,
            )
            applied = set_desktop(last_path)
            if applied is False:
                logging.warning(
                    "Wallpaper re-apply failed; leaving run state unchanged: %s",
                    last_path,
                )
                return
            _remember_applied(
                applied_run_state,
                run_key=run_key,
                wallpaper_path=last_path,
                record_run_key=True,
            )
            return

    pic = Pic(time_str, grade, base_dir=base_dir)
    create_pic_folders(pic)
    download(pic)
    if not pic.download_finish():
        logging.warning("Not all tiles downloaded; skipping compose and wallpaper apply")
        return
    if use_direct_margin_compose:
        wallpaper_path = compose_equal_image_with_margins(
            pic,
            _adjusted_output_path(pic),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
        )
    else:
        compose(pic)
        wallpaper_path = adjust(pic) if auto_adjust else Path(pic.final_path_equal)
    applied = set_desktop(wallpaper_path)
    if applied is False:
        logging.warning(
            "Wallpaper apply failed or skipped; leaving run state and cache unchanged: %s",
            wallpaper_path,
        )
        return
    _remember_applied(
        applied_run_state,
        run_key=run_key,
        wallpaper_path=Path(wallpaper_path),
        record_run_key=record_run_key,
    )
    if cleanup_after_apply:
        current_run_root = Path(pic.folder_path).parent
        cleanup_after_wallpaper_apply(
            img_root=pic.base_dir / pic.folder_top,
            current_run_root=current_run_root,
            keep_file=Path(wallpaper_path),
        )
    logging.info("Wallpaper pipeline finished: %s", wallpaper_path)
