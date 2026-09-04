"""壁纸更新流水线：编排观测时间→瓦片→等分合成图→可选修边→可选台风标注→设桌面→可选清理。"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable, MutableMapping
from pathlib import Path
from time import strftime, strptime, struct_time
from typing import Any

from PIL import Image

from src.compose.equal import (
    apply_margins,
    compose_equal_image,
    compose_equal_image_with_margins,
    compute_margin_layout,
    get_primary_screen_size,
)
from src.compose.geo import latlon_to_himawari_fd_xy
from src.compose.overlay import draw_typhoon_marker
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
from src.resolution_grade import default_grade, grade_to_pixel
from src.wallpaper.cleanup import cleanup_after_wallpaper_apply
from src.wallpaper.desktop import get_desktop_wallpaper as read_desktop_wallpaper
from src.wallpaper.desktop import set_wallpaper as apply_desktop_wallpaper
from src.wallpaper.desktop import wallpaper_paths_match
from src.wallpaper.folders import create_pic_folders

FetchObservationTime = Callable[[], struct_time]
DownloadTiles = Callable[[Pic], None]
ComposeEqual = Callable[[Pic], None]
AdjustWallpaper = Callable[[Pic], Path]
SetWallpaper = Callable[[Path], bool | None]
GetDesktopWallpaper = Callable[[], str | None]
FetchTyphoonCenter = Callable[[struct_time], tuple[float, float] | None]
AppliedRunState = MutableMapping[str, Any]
AppliedRunKey = tuple[str, str, bool, float, float, bool, bool]

_OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"


def _default_fetch_observation_time() -> struct_time:
    return fetch_latest_observation_time(create_session())


def _default_download_tiles(pic: Pic) -> None:
    download_tiles(pic)


def _default_set_wallpaper(path: Path) -> bool | None:
    return apply_desktop_wallpaper(path)


def _adjusted_output_path(pic: Pic) -> Path:
    src = Path(pic.final_path_equal)
    return src.with_name(f"{src.stem}_adjust{src.suffix}")


def wallpaper_base_path(wallpaper_path: Path) -> Path:
    """无台风标记底图路径：``{stem}_base{suffix}``。"""
    return wallpaper_path.with_name(f"{wallpaper_path.stem}_base{wallpaper_path.suffix}")


def build_applied_run_key(
    observation_time: struct_time,
    *,
    resolution_grade: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool = False,
    show_typhoon_marker: bool = False,
) -> AppliedRunKey:
    """用于判断是否可跳过重复下载的指纹（观测时间 + 影响成图的参数）。"""
    return (
        strftime(_OBS_TIME_FMT, observation_time),
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
        bool(reduce_banding),
        bool(show_typhoon_marker),
    )


def _remember_applied(
    applied_run_state: AppliedRunState | None,
    *,
    run_key: AppliedRunKey,
    wallpaper_path: Path,
    wallpaper_base: Path | None = None,
    record_run_key: bool,
) -> None:
    if applied_run_state is None:
        return
    # 展示用：即使不写跳过指纹，也记下实际上墙档位。
    applied_run_state["applied_grade"] = run_key[1]
    if record_run_key:
        applied_run_state["last"] = run_key
    try:
        applied_run_state["wallpaper_path"] = str(wallpaper_path.resolve())
    except OSError:
        applied_run_state["wallpaper_path"] = str(wallpaper_path)
    base = wallpaper_base if wallpaper_base is not None else wallpaper_base_path(wallpaper_path)
    try:
        applied_run_state["wallpaper_base_path"] = str(base.resolve())
    except OSError:
        applied_run_state["wallpaper_base_path"] = str(base)


def _ensure_unmarked_base(wallpaper_path: Path) -> Path:
    """把当前无标记成品复制为 ``*_base``（已存在则不覆盖）。"""
    base = wallpaper_base_path(wallpaper_path)
    if base.is_file():
        return base
    if not wallpaper_path.is_file():
        return base
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper_path, base)
    return base


def _resolve_base_path(
    applied_run_state: AppliedRunState | None,
    wallpaper_path: Path,
) -> Path:
    if applied_run_state is not None:
        raw = applied_run_state.get("wallpaper_base_path")
        if isinstance(raw, str) and raw.strip():
            candidate = Path(raw.strip())
            if candidate.is_file():
                return candidate
    return wallpaper_base_path(wallpaper_path)


def _typhoon_flag_only_differs(last: Any, run_key: AppliedRunKey) -> bool:
    return (
        isinstance(last, tuple)
        and len(last) == 7
        and last[:6] == run_key[:6]
        and bool(last[6]) != bool(run_key[6])
    )


def _provisional_run_key_from_last(
    last: Any,
    *,
    resolution_grade: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool,
    show_typhoon_marker: bool,
) -> AppliedRunKey | None:
    """用上次指纹的观测时间 + 当前成图参数拼临时指纹（不访问网络）。"""
    if not isinstance(last, tuple) or len(last) < 1 or not isinstance(last[0], str):
        return None
    return (
        last[0],
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
        bool(reduce_banding),
        bool(show_typhoon_marker),
    )


def _apply_typhoon_marker_if_needed(
    *,
    wallpaper_path: Path,
    pic_side: int,
    observation_time: struct_time,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    fetch_typhoon_center_fn: FetchTyphoonCenter,
) -> None:
    """在最终壁纸文件上标注台风中心；失败只记日志。"""
    center = fetch_typhoon_center_fn(observation_time)
    if center is None:
        return
    lat, lon = center
    xy = latlon_to_himawari_fd_xy(lat, lon, pic_side)
    if xy is None:
        logging.info("Typhoon center projects outside full-disk frame; skipping marker")
        return
    draw_xy = xy
    if auto_adjust:
        try:
            with Image.open(wallpaper_path) as img:
                canvas_w, canvas_h = img.size
        except OSError:
            logging.exception("Failed to open wallpaper for typhoon marker offset: %s", wallpaper_path)
            return
        if canvas_w != pic_side or canvas_h != pic_side:
            screen_width, screen_height = get_primary_screen_size()
            _, _, image_x, image_y = compute_margin_layout(
                pic_side,
                screen_width,
                screen_height,
                top_percent=margin_top_percent,
                bottom_percent=margin_bottom_percent,
            )
            draw_xy = (image_x + xy[0], image_y + xy[1])
    draw_typhoon_marker(wallpaper_path, draw_xy)


def _try_typhoon_marker_fast_path(
    *,
    applied_run_state: AppliedRunState,
    run_key: AppliedRunKey,
    observation_time_struct: struct_time,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    show_typhoon_marker: bool,
    set_desktop: SetWallpaper,
    typhoon_fetch: FetchTyphoonCenter,
    record_run_key: bool,
) -> str | None:
    """仅台风开关变化且成品仍在时：复用底图，不下载瓦片。

    Returns:
        成功时返回观测时间字符串；无法走快路径时 ``None``（调用方应继续全量）。
    """
    last = applied_run_state.get("last")
    if not _typhoon_flag_only_differs(last, run_key):
        return None

    last_path_raw = applied_run_state.get("wallpaper_path")
    if not isinstance(last_path_raw, str) or not last_path_raw.strip():
        return None
    wallpaper_path = Path(last_path_raw.strip())
    base = _resolve_base_path(applied_run_state, wallpaper_path)

    # 上一轮无标记且未写 base：当前成品即底图。
    if not base.is_file() and wallpaper_path.is_file() and not bool(last[6]):
        try:
            base = _ensure_unmarked_base(wallpaper_path)
        except OSError:
            logging.exception("Failed to create unmarked base from %s", wallpaper_path)
            return None

    if not base.is_file():
        logging.info("Typhoon fast path skipped: unmarked base missing (%s)", base)
        return None

    observation_time = run_key[0]
    pic_side = grade_to_pixel(run_key[1])

    try:
        if show_typhoon_marker:
            shutil.copy2(base, wallpaper_path)
            _apply_typhoon_marker_if_needed(
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                observation_time=observation_time_struct,
                auto_adjust=auto_adjust,
                margin_top_percent=margin_top_percent,
                margin_bottom_percent=margin_bottom_percent,
                fetch_typhoon_center_fn=typhoon_fetch,
            )
            apply_path = wallpaper_path
            logging.info("Typhoon marker fast path: overlaid on existing wallpaper")
        else:
            shutil.copy2(base, wallpaper_path)
            apply_path = wallpaper_path
            logging.info("Typhoon marker fast path: restored unmarked base")
    except OSError:
        logging.exception("Typhoon fast path failed while copying base/wallpaper")
        return None

    if not apply_path.is_file():
        return None

    applied = set_desktop(apply_path)
    if applied is False:
        logging.warning("Typhoon fast path: wallpaper apply failed: %s", apply_path)
        return None

    _remember_applied(
        applied_run_state,
        run_key=run_key,
        wallpaper_path=apply_path,
        wallpaper_base=base,
        record_run_key=record_run_key,
    )
    return observation_time


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
    - 仅台风开关变化且无标记底图仍在 → 用上次观测时间叠加/复原，不拉 latest、不下载；
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
    use_direct_margin_compose = auto_adjust and compose_equal is None and adjust_wallpaper is None

    def default_adjust(pic: Pic) -> Path:
        out = _adjusted_output_path(pic)
        apply_margins(
            str(pic.final_path_equal),
            pic.pic_side,
            str(out),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
            deband=reduce_banding,
        )
        return out

    adjust = adjust_wallpaper or default_adjust

    # 台风开关快路径：在拉 latest.json 之前用上次指纹观测时间复用成品，避免网络卡住。
    if applied_run_state is not None:
        last = applied_run_state.get("last")
        provisional = _provisional_run_key_from_last(
            last,
            resolution_grade=grade,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            reduce_banding=reduce_banding,
            show_typhoon_marker=show_typhoon_marker,
        )
        if provisional is not None and _typhoon_flag_only_differs(last, provisional):
            try:
                obs_struct = strptime(provisional[0], _OBS_TIME_FMT)
            except ValueError:
                obs_struct = None
            if obs_struct is not None:
                fast = _try_typhoon_marker_fast_path(
                    applied_run_state=applied_run_state,
                    run_key=provisional,
                    observation_time_struct=obs_struct,
                    auto_adjust=auto_adjust,
                    margin_top_percent=margin_top_percent,
                    margin_bottom_percent=margin_bottom_percent,
                    show_typhoon_marker=show_typhoon_marker,
                    set_desktop=set_desktop,
                    typhoon_fetch=typhoon_fetch,
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
            _remember_applied(
                applied_run_state,
                run_key=run_key,
                wallpaper_path=last_path,
                record_run_key=True,
            )
            return observation_time

    # 观测时间已刷新后再试一次（例如 last 观测与 latest 相同、仅台风位不同）。
    if applied_run_state is not None:
        fast = _try_typhoon_marker_fast_path(
            applied_run_state=applied_run_state,
            run_key=run_key,
            observation_time_struct=time_str,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            show_typhoon_marker=show_typhoon_marker,
            set_desktop=set_desktop,
            typhoon_fetch=typhoon_fetch,
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
    if use_direct_margin_compose:
        wallpaper_path = compose_equal_image_with_margins(
            pic,
            _adjusted_output_path(pic),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
            deband=reduce_banding,
        )
    else:
        if compose_equal is None:
            compose_equal_image(pic, deband=reduce_banding and not auto_adjust)
        else:
            compose_equal(pic)
        wallpaper_path = adjust(pic) if auto_adjust else Path(pic.final_path_equal)

    wallpaper_path = Path(wallpaper_path)
    try:
        base_path = _ensure_unmarked_base(wallpaper_path)
    except OSError:
        logging.exception("Failed to save unmarked wallpaper base: %s", wallpaper_path)
        base_path = wallpaper_base_path(wallpaper_path)

    if show_typhoon_marker:
        _apply_typhoon_marker_if_needed(
            wallpaper_path=wallpaper_path,
            pic_side=pic.pic_side,
            observation_time=time_str,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            fetch_typhoon_center_fn=typhoon_fetch,
        )
    applied = set_desktop(wallpaper_path)
    if applied is False:
        logging.warning(
            "Wallpaper apply failed or skipped; leaving run state and cache unchanged: %s",
            wallpaper_path,
        )
        return None
    _remember_applied(
        applied_run_state,
        run_key=run_key,
        wallpaper_path=wallpaper_path,
        wallpaper_base=base_path,
        record_run_key=record_run_key,
    )
    if cleanup_after_apply:
        current_run_root = Path(pic.folder_path).parent
        keep = [wallpaper_path]
        if base_path.is_file():
            keep.append(base_path)
        cleanup_after_wallpaper_apply(
            img_root=pic.base_dir / pic.folder_top,
            current_run_root=current_run_root,
            keep_files=keep,
        )
    logging.info("Wallpaper pipeline finished: %s", wallpaper_path)
    return observation_time
