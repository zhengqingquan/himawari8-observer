"""壁纸更新流水线：编排观测时间→瓦片→等分合成图→可选修边→可选台风标注→设桌面→可选清理。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from time import struct_time

from src.compose.equal import apply_deband_to_file, apply_margins, compose_equal_image
from src.download.observation import create_session
from src.download.observation import fetch_observation_time as fetch_latest_observation_time
from src.download.observation import observation_time_yesterday_local
from src.download.tiles import download_tiles
from src.download.typhoon import fetch_typhoon_center
from src.metadata.app_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)
from src.pic import Pic
from src.resolution_grade import default_grade
from src.wallpaper.cleanup import cleanup_after_wallpaper_apply
from src.wallpaper.desktop import get_desktop_wallpaper as read_desktop_wallpaper
from src.wallpaper.desktop import set_wallpaper as apply_desktop_wallpaper
from src.wallpaper.desktop import wallpaper_paths_match
from src.wallpaper.folders import create_pic_folders
from src.wallpaper.postprocess import (
    AppliedRunState,
    apply_typhoon_marker_if_needed,
    build_applied_run_key,
    equal_path_from_disk,
    layout_or_postprocess_differs,
    provisional_run_key_from_last,
    remember_applied,
    save_disk_copy,
    save_unmarked_base,
    try_postprocess_fast_path,
    wallpaper_base_path,
    wallpaper_disk_path,
    wallpaper_output_path,
)

# 对外仍可从 pipeline 导入路径/指纹辅助（兼容既有引用）。
__all__ = [
    "run_wallpaper_pipeline",
    "build_applied_run_key",
    "wallpaper_base_path",
    "wallpaper_disk_path",
    "equal_path_from_disk",
    "wallpaper_output_path",
]

FetchObservationTime = Callable[[], struct_time]
DownloadTiles = Callable[[Pic], None]
ComposeEqual = Callable[[Pic], None]
AdjustWallpaper = Callable[[Pic], Path]
SetWallpaper = Callable[[Path], bool | None]
GetDesktopWallpaper = Callable[[], str | None]
FetchTyphoonCenter = Callable[[struct_time], tuple[float, float] | None]


def _default_fetch_observation_time() -> struct_time:
    return fetch_latest_observation_time(create_session())


def _default_download_tiles(pic: Pic) -> None:
    download_tiles(pic)


def _default_set_wallpaper(path: Path) -> bool | None:
    return apply_desktop_wallpaper(path)


def _adjusted_output_path(pic: Pic) -> Path:
    src = Path(pic.final_path_equal)
    return src.with_name(f"{src.stem}_adjust{src.suffix}")


def run_wallpaper_pipeline(
    *,
    fetch_observation_time: FetchObservationTime | None = None,
    download_tiles: DownloadTiles | None = None,
    compose_equal: ComposeEqual | None = None,
    adjust_wallpaper: AdjustWallpaper | None = None,
    set_wallpaper: SetWallpaper | None = None,
    get_desktop_wallpaper: GetDesktopWallpaper | None = None,
    fetch_typhoon_center_fn: FetchTyphoonCenter | None = None,
    resolution_grade: str | None = None,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    cleanup_after_apply: bool = True,
    use_yesterday_local_time: bool = False,
    reduce_banding: bool = False,
    show_typhoon_marker: bool = False,
    base_dir: Path | None = None,
    applied_run_state: AppliedRunState | None = None,
    record_run_key: bool = True,
) -> str | None:
    """跑一次壁纸更新。副作用步骤可注入，便于测试。

    托盘 / 定时器只应通过 WallpaperJobRef 触发，不要直接 import 本模块或 download/。

    跳过策略（需 ``applied_run_state``）：
    - 同观测/档位下仅修边或色带/台风变化且 disk/base 仍在 → 从中间图重建，不拉 latest、不下载；
    - 自动跟 latest 时若观测时间早于已应用 → 跳过（防源站回退导致往回刷）；
    - 指纹相同且桌面仍是上次壁纸文件 → 整段跳过；
    - 指纹相同但桌面已换、成品仍在 → 仅重设壁纸；
    - 否则走完整流水线。

    Returns:
        成功上墙（含仅重设）时返回观测时间 ``YYYY-MM-DD HH:MM:SS``（UTC）；
        跳过或失败时返回 ``None``。``record_run_key=False`` 时仍可能返回时间（供展示），
        但不写入跳过指纹。
    """
    fetch = fetch_observation_time or _default_fetch_observation_time
    download = download_tiles or _default_download_tiles
    set_desktop = set_wallpaper or _default_set_wallpaper
    read_desktop = get_desktop_wallpaper or read_desktop_wallpaper
    typhoon_fetch = fetch_typhoon_center_fn or fetch_typhoon_center
    grade = resolution_grade if resolution_grade is not None else default_grade()

    def default_adjust(pic: Pic) -> Path:
        out = _adjusted_output_path(pic)
        apply_margins(
            str(pic.final_path_equal),
            pic.pic_side,
            str(out),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
            deband=False,
        )
        return out

    adjust = adjust_wallpaper or default_adjust

    # 后处理快路径：在拉 latest.json 之前用上次指纹观测时间从中间图重建，避免网络卡住。
    if applied_run_state is not None:
        last = applied_run_state.get("last")
        provisional = provisional_run_key_from_last(
            last,
            resolution_grade=grade,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            reduce_banding=reduce_banding,
            show_typhoon_marker=show_typhoon_marker,
        )
        if provisional is not None and layout_or_postprocess_differs(last, provisional):
            fast = try_postprocess_fast_path(
                applied_run_state=applied_run_state,
                run_key=provisional,
                auto_adjust=auto_adjust,
                margin_top_percent=margin_top_percent,
                margin_bottom_percent=margin_bottom_percent,
                reduce_banding=reduce_banding,
                show_typhoon_marker=show_typhoon_marker,
                set_desktop=set_desktop,
                record_run_key=record_run_key,
            )
            if fast is not None:
                return fast

    if use_yesterday_local_time:
        time_str = observation_time_yesterday_local()
    else:
        time_str = fetch()
    run_key = build_applied_run_key(
        time_str,
        resolution_grade=grade,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
        reduce_banding=reduce_banding,
        show_typhoon_marker=show_typhoon_marker,
    )
    observation_time = run_key[0]
    if not use_yesterday_local_time and applied_run_state is not None:
        last = applied_run_state.get("last")
        if (
            isinstance(last, tuple)
            and len(last) >= 1
            and isinstance(last[0], str)
            and observation_time < last[0]
        ):
            logging.info(
                "Latest observation %s is older than applied %s; skipping update",
                observation_time,
                last[0],
            )
            return None
    if applied_run_state is not None and applied_run_state.get("last") == run_key:
        last_path_raw = applied_run_state.get("wallpaper_path")
        last_path = Path(last_path_raw) if last_path_raw else None
        if last_path is not None and last_path.is_file():
            current_desktop = read_desktop()
            if wallpaper_paths_match(current_desktop, last_path):
                logging.info(
                    "Observation params unchanged and desktop wallpaper still ours; skipping update"
                )
                return None
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
                return None
            remember_applied(
                applied_run_state,
                run_key=run_key,
                wallpaper_path=last_path,
                record_run_key=True,
            )
            return observation_time

    # 观测时间已刷新后再试一次（例如 last 观测与 latest 相同、仅后处理开关不同）。
    if applied_run_state is not None:
        fast = try_postprocess_fast_path(
            applied_run_state=applied_run_state,
            run_key=run_key,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            reduce_banding=reduce_banding,
            show_typhoon_marker=show_typhoon_marker,
            set_desktop=set_desktop,
            record_run_key=record_run_key,
        )
        if fast is not None:
            return fast

    pic = Pic(time_str, grade, base_dir=base_dir)
    create_pic_folders(pic)
    download(pic)
    if not pic.download_finish():
        logging.warning("Not all tiles downloaded; skipping compose and wallpaper apply")
        return None
    # 始终先落等分圆盘，再修边；保留 *_disk 供改边距时后处理。
    if compose_equal is None:
        compose_equal_image(pic, deband=False)
    else:
        compose_equal(pic)
    equal_path = Path(pic.final_path_equal)
    try:
        disk_path = save_disk_copy(equal_path)
    except OSError:
        logging.exception("Failed to save equal disk copy: %s", equal_path)
        disk_path = wallpaper_disk_path(equal_path)

    wallpaper_path = adjust(pic) if auto_adjust else equal_path
    wallpaper_path = Path(wallpaper_path)
    try:
        base_path = save_unmarked_base(wallpaper_path)
    except OSError:
        logging.exception("Failed to save unmarked wallpaper base: %s", wallpaper_path)
        base_path = wallpaper_base_path(wallpaper_path)

    if reduce_banding:
        try:
            apply_deband_to_file(base_path, wallpaper_path)
        except OSError:
            logging.exception("Failed to apply deband to wallpaper: %s", wallpaper_path)
            return None

    if show_typhoon_marker:
        apply_typhoon_marker_if_needed(
            wallpaper_path=wallpaper_path,
            pic_side=pic.pic_side,
            observation_time=time_str,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            fetch_typhoon_center_fn=typhoon_fetch,
            applied_run_state=applied_run_state,
        )
    applied = set_desktop(wallpaper_path)
    if applied is False:
        logging.warning(
            "Wallpaper apply failed or skipped; leaving run state and cache unchanged: %s",
            wallpaper_path,
        )
        return None
    remember_applied(
        applied_run_state,
        run_key=run_key,
        wallpaper_path=wallpaper_path,
        wallpaper_base=base_path,
        wallpaper_disk=disk_path,
        record_run_key=record_run_key,
    )
    if cleanup_after_apply:
        current_run_root = Path(pic.folder_path).parent
        keep = [wallpaper_path]
        if base_path.is_file():
            keep.append(base_path)
        if disk_path.is_file():
            keep.append(disk_path)
        cleanup_after_wallpaper_apply(
            img_root=pic.base_dir / pic.folder_top,
            current_run_root=current_run_root,
            keep_files=keep,
        )
    logging.info("Wallpaper pipeline finished: %s", wallpaper_path)
    return observation_time
