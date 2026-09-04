"""后处理快路径：同观测/档位下从 disk/base 重建成品（不拉 latest、不下载瓦片）。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from src.compose.equal import apply_deband_to_file, apply_margins
from src.resolution_grade import grade_to_pixel
from src.wallpaper.fingerprint import (
    AppliedRunKey,
    layout_or_postprocess_differs,
    remember_applied,
)
from src.wallpaper.markers import (
    FetchIpLatlon,
    FetchTyphoonCenter,
    apply_my_location_marker_if_needed,
    apply_typhoon_marker_cached_or_fetch,
)
from src.wallpaper.paths import (
    AppliedRunState,
    alternate_wallpaper_path,
    copy2_wallpaper,
    ensure_unmarked_base,
    equal_path_from_disk,
    pick_writable_wallpaper_path,
    resolve_base_path,
    resolve_disk_path,
    save_unmarked_base,
    wallpaper_output_path,
)

SetWallpaper = Callable[[Path], bool | None]
GetDesktopWallpaper = Callable[[], str | None]


def _rebuild_from_base(
    *,
    applied_run_state: AppliedRunState,
    last: AppliedRunKey,
    last_wallpaper: Path,
    wallpaper_path: Path,
    reduce_banding: bool,
) -> tuple[Path, Path] | None:
    """布局未变：从 ``*_base`` 重建成品（可从无标记成品回填 base）。

    Returns:
        ``(base, written_wallpaper_path)``；无法重建时 ``None``。
    """
    base = resolve_base_path(applied_run_state, last_wallpaper)
    if (
        not base.is_file()
        and last_wallpaper.is_file()
        and not last.reduce_banding
        and not last.show_typhoon_marker
        and not last.show_my_location
    ):
        try:
            base = ensure_unmarked_base(last_wallpaper)
        except OSError:
            logging.exception("Failed to create unmarked base from %s", last_wallpaper)
            return None
    if not base.is_file():
        logging.info("Postprocess fast path skipped: unmarked base missing (%s)", base)
        return None
    if reduce_banding:
        try:
            apply_deband_to_file(base, wallpaper_path)
            written = wallpaper_path
        except OSError as exc:
            if getattr(exc, "winerror", None) != 1224:
                raise
            written = alternate_wallpaper_path(wallpaper_path)
            logging.info(
                "deband hit WinError 1224 on %s; writing to %s",
                wallpaper_path,
                written,
            )
            apply_deband_to_file(base, written)
    else:
        written = copy2_wallpaper(base, wallpaper_path)
    return base, written


def _rebuild_from_disk(
    *,
    disk: Path,
    wallpaper_path: Path,
    pic_side: int,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool,
) -> tuple[Path, Path] | None:
    """边距/修边变了：从 ``*_disk`` 再修边，写入新 base，可选去色带。

    Returns:
        ``(base, written_wallpaper_path)``；无法重建时 ``None``。
    """
    if not disk.is_file():
        logging.info("Postprocess fast path skipped: equal disk missing (%s)", disk)
        return None
    wallpaper_path.parent.mkdir(parents=True, exist_ok=True)
    written = wallpaper_path
    try:
        if auto_adjust:
            apply_margins(
                str(disk),
                pic_side,
                str(written),
                top_percent=margin_top_percent,
                bottom_percent=margin_bottom_percent,
                deband=False,
            )
        else:
            written = copy2_wallpaper(disk, written)
    except OSError as exc:
        if getattr(exc, "winerror", None) != 1224:
            raise
        written = alternate_wallpaper_path(wallpaper_path)
        logging.info(
            "rebuild-from-disk hit WinError 1224 on %s; writing to %s",
            wallpaper_path,
            written,
        )
        if auto_adjust:
            apply_margins(
                str(disk),
                pic_side,
                str(written),
                top_percent=margin_top_percent,
                bottom_percent=margin_bottom_percent,
                deband=False,
            )
        else:
            written = copy2_wallpaper(disk, written)
    base = save_unmarked_base(written)
    if reduce_banding:
        apply_deband_to_file(base, written)
    return base, written


def try_postprocess_fast_path(
    *,
    applied_run_state: AppliedRunState,
    run_key: AppliedRunKey,
    set_desktop: SetWallpaper,
    record_run_key: bool,
    fetch_ip_latlon_fn: FetchIpLatlon | None = None,
    fetch_typhoon_center_fn: FetchTyphoonCenter | None = None,
    get_desktop: GetDesktopWallpaper | None = None,
) -> str | None:
    """同观测/档位下仅修边或色带/台风/定位变化时：从 disk/base 重建成品。

    不拉 ``latest.json``、不下载瓦片。台风/定位在缓存未命中时可各请求一次（与全量同 seam）。

    Returns:
        成功时返回观测时间字符串；无法走快路径时 ``None``（调用方应继续全量）。
    """
    last = AppliedRunKey.from_raw(applied_run_state.get("last"))
    if last is None or not layout_or_postprocess_differs(last, run_key):
        return None

    options = run_key.options
    last_path_raw = applied_run_state.get("wallpaper_path")
    if not isinstance(last_path_raw, str) or not last_path_raw.strip():
        return None
    last_wallpaper = Path(last_path_raw.strip())
    layout_same = last.layout == run_key.layout
    observation_time = run_key.observation_time
    pic_side = grade_to_pixel(run_key.resolution_grade)
    disk = resolve_disk_path(applied_run_state, last_wallpaper)
    equal_path = equal_path_from_disk(disk)
    preferred = (
        last_wallpaper
        if layout_same
        else wallpaper_output_path(equal_path, auto_adjust=options.auto_adjust)
    )
    current_desktop = get_desktop() if get_desktop is not None else None
    wallpaper_path = pick_writable_wallpaper_path(
        preferred,
        current_desktop=current_desktop,
    )

    try:
        if layout_same:
            # 同布局：复用 *_base（色带/台风/定位开关变化）。
            rebuilt = _rebuild_from_base(
                applied_run_state=applied_run_state,
                last=last,
                last_wallpaper=last_wallpaper,
                wallpaper_path=wallpaper_path,
                reduce_banding=options.reduce_banding,
            )
        else:
            # 修边/边距变了：从 *_disk 重建。
            rebuilt = _rebuild_from_disk(
                disk=disk,
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                auto_adjust=options.auto_adjust,
                margin_top_percent=options.margin_top_percent,
                margin_bottom_percent=options.margin_bottom_percent,
                reduce_banding=options.reduce_banding,
            )
        if rebuilt is None:
            return None
        base, wallpaper_path = rebuilt

        if options.show_typhoon_marker:
            # 同帧缓存优先；未命中（如全量时超时未写入）则回退拉一次 D531108。
            apply_typhoon_marker_cached_or_fetch(
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                observation_time=observation_time,
                auto_adjust=options.auto_adjust,
                margin_top_percent=options.margin_top_percent,
                margin_bottom_percent=options.margin_bottom_percent,
                applied_run_state=applied_run_state,
                fetch_typhoon_center_fn=fetch_typhoon_center_fn,
                allow_network=True,
            )
        if options.show_my_location:
            # IP 定位与观测时间无关：快路径无缓存时允许联网，避免首次开启永远不画。
            apply_my_location_marker_if_needed(
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                auto_adjust=options.auto_adjust,
                margin_top_percent=options.margin_top_percent,
                margin_bottom_percent=options.margin_bottom_percent,
                fetch_ip_latlon_fn=fetch_ip_latlon_fn or (lambda: None),
                applied_run_state=applied_run_state,
                allow_network=True,
            )
        logging.info(
            "Postprocess fast path: rebuilt wallpaper "
            "(layout_same=%s banding=%s typhoon=%s my_location=%s)",
            layout_same,
            options.reduce_banding,
            options.show_typhoon_marker,
            options.show_my_location,
        )
    except OSError:
        logging.exception("Postprocess fast path failed while rebuilding wallpaper")
        return None

    if not wallpaper_path.is_file():
        return None

    applied = set_desktop(wallpaper_path)
    if applied is False:
        logging.warning("Postprocess fast path: wallpaper apply failed: %s", wallpaper_path)
        return None

    remember_applied(
        applied_run_state,
        run_key=run_key,
        wallpaper_path=wallpaper_path,
        wallpaper_base=base,
        wallpaper_disk=disk if disk.is_file() else None,
        record_run_key=record_run_key,
    )
    return observation_time
