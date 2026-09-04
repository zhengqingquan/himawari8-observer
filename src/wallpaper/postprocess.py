"""成图指纹、中间路径命名、后处理快路径与台风/定位标注辅助。"""

from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from time import strftime, struct_time
from typing import Any, MutableMapping, NamedTuple

from PIL import Image

from src.compose.equal import (
    apply_deband_to_file,
    apply_margins,
    compute_margin_layout,
    get_primary_screen_size,
)
from src.compose.geo import latlon_to_himawari_fd_xy
from src.compose.overlay import draw_typhoon_marker
from src.resolution_grade import grade_to_pixel

AppliedRunState = MutableMapping[str, Any]
SetWallpaper = Callable[[Path], bool | None]
FetchTyphoonCenter = Callable[[struct_time], tuple[float, float] | None]
FetchIpLatlon = Callable[[], tuple[float, float] | None]

_OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"
_MY_LOCATION_CACHE_TTL_SEC = 24 * 60 * 60
_MY_LOCATION_MARKER_COLOR = (64, 156, 255)
_MY_LOCATION_MARKER_LABEL = "ME"


class AppliedRunKey(NamedTuple):
    """成图指纹：观测时间 + 影响成品的参数（落盘仍为 8 项 list）。"""

    observation_time: str
    resolution_grade: str
    auto_adjust: bool
    margin_top_percent: float
    margin_bottom_percent: float
    reduce_banding: bool
    show_typhoon_marker: bool
    show_my_location: bool

    @property
    def layout(self) -> tuple[bool, float, float]:
        """修边开关与上下边距（与色带/台风/定位无关）。"""
        return (
            self.auto_adjust,
            self.margin_top_percent,
            self.margin_bottom_percent,
        )

    @classmethod
    def from_raw(cls, value: Any) -> AppliedRunKey | None:
        """接受本类型或 5/6/7/8 项序列（缺省布尔为 ``False``）；非法则 ``None``。"""
        if isinstance(value, cls):
            return value
        if not isinstance(value, (tuple, list)) or len(value) not in (5, 6, 7, 8):
            return None
        try:
            obs_time = str(value[0])
            grade = str(value[1])
            auto_adjust = bool(value[2])
            top = float(value[3])
            bottom = float(value[4])
            reduce_banding = bool(value[5]) if len(value) >= 6 else False
            show_typhoon = bool(value[6]) if len(value) >= 7 else False
            show_my_location = bool(value[7]) if len(value) == 8 else False
        except (TypeError, ValueError):
            return None
        if not obs_time or not grade:
            return None
        return cls(
            obs_time,
            grade,
            auto_adjust,
            top,
            bottom,
            reduce_banding,
            show_typhoon,
            show_my_location,
        )


def wallpaper_base_path(wallpaper_path: Path) -> Path:
    """未去色带、无台风/定位标记的底图路径：``{stem}_base{suffix}``。"""
    return wallpaper_path.with_name(f"{wallpaper_path.stem}_base{wallpaper_path.suffix}")


def wallpaper_disk_path(equal_or_wallpaper: Path) -> Path:
    """等分圆盘（未修边）路径：由等分图或 ``*_adjust`` 成品推导 ``{stem}_disk``。"""
    stem = equal_or_wallpaper.stem
    if stem.endswith("_adjust"):
        stem = stem[: -len("_adjust")]
    elif stem.endswith("_disk"):
        return equal_or_wallpaper
    return equal_or_wallpaper.with_name(f"{stem}_disk{equal_or_wallpaper.suffix}")


def equal_path_from_disk(disk_path: Path) -> Path:
    """由 ``*_disk`` 还原等分图路径。"""
    stem = disk_path.stem
    if stem.endswith("_disk"):
        stem = stem[: -len("_disk")]
    return disk_path.with_name(f"{stem}{disk_path.suffix}")


def wallpaper_output_path(equal_path: Path, *, auto_adjust: bool) -> Path:
    """按是否修边决定成品路径（修边为 ``*_adjust``）。"""
    if auto_adjust:
        return equal_path.with_name(f"{equal_path.stem}_adjust{equal_path.suffix}")
    return equal_path


def build_applied_run_key(
    observation_time: struct_time,
    *,
    resolution_grade: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool = False,
    show_typhoon_marker: bool = False,
    show_my_location: bool = False,
) -> AppliedRunKey:
    """用于判断是否可跳过重复下载的指纹（观测时间 + 影响成图的参数）。"""
    return AppliedRunKey(
        strftime(_OBS_TIME_FMT, observation_time),
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
        bool(reduce_banding),
        bool(show_typhoon_marker),
        bool(show_my_location),
    )


def _path_str(path: Path) -> str:
    """优先 ``resolve()`` 的绝对路径字符串；失败则退回 ``str(path)``。"""
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def remember_applied(
    applied_run_state: AppliedRunState | None,
    *,
    run_key: AppliedRunKey,
    wallpaper_path: Path,
    wallpaper_base: Path | None = None,
    wallpaper_disk: Path | None = None,
    record_run_key: bool,
) -> None:
    if applied_run_state is None:
        return
    # 展示用：即使不写跳过指纹，也记下实际上墙档位。
    applied_run_state["applied_grade"] = run_key.resolution_grade
    if record_run_key:
        applied_run_state["last"] = run_key
    applied_run_state["wallpaper_path"] = _path_str(wallpaper_path)
    base = wallpaper_base if wallpaper_base is not None else wallpaper_base_path(wallpaper_path)
    applied_run_state["wallpaper_base_path"] = _path_str(base)
    disk = wallpaper_disk if wallpaper_disk is not None else wallpaper_disk_path(wallpaper_path)
    applied_run_state["wallpaper_disk_path"] = _path_str(disk)


def ensure_unmarked_base(wallpaper_path: Path) -> Path:
    """若 ``*_base`` 缺失，把当前成品复制为底图（已存在则不覆盖）。"""
    base = wallpaper_base_path(wallpaper_path)
    if base.is_file():
        return base
    if not wallpaper_path.is_file():
        return base
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper_path, base)
    return base


def save_unmarked_base(wallpaper_path: Path) -> Path:
    """将当前成品（须为未去色带、无台风标记）写入 ``*_base``（覆盖）。"""
    base = wallpaper_base_path(wallpaper_path)
    if not wallpaper_path.is_file():
        return base
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper_path, base)
    return base


def save_disk_copy(equal_path: Path) -> Path:
    """将等分圆盘复制为 ``*_disk``（覆盖），供修边后处理复用。"""
    disk = wallpaper_disk_path(equal_path)
    if not equal_path.is_file():
        return disk
    disk.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(equal_path, disk)
    return disk


def _resolve_state_path(
    applied_run_state: AppliedRunState | None,
    key: str,
    wallpaper_path: Path,
    fallback: Callable[[Path], Path],
) -> Path:
    """若 state 中 ``key`` 指向现存文件则用之，否则 ``fallback(wallpaper_path)``。"""
    if applied_run_state is not None:
        raw = applied_run_state.get(key)
        if isinstance(raw, str) and raw.strip():
            candidate = Path(raw.strip())
            if candidate.is_file():
                return candidate
    return fallback(wallpaper_path)


def resolve_base_path(
    applied_run_state: AppliedRunState | None,
    wallpaper_path: Path,
) -> Path:
    return _resolve_state_path(
        applied_run_state,
        "wallpaper_base_path",
        wallpaper_path,
        wallpaper_base_path,
    )


def resolve_disk_path(
    applied_run_state: AppliedRunState | None,
    wallpaper_path: Path,
) -> Path:
    return _resolve_state_path(
        applied_run_state,
        "wallpaper_disk_path",
        wallpaper_path,
        wallpaper_disk_path,
    )


def obs_grade_match(last: AppliedRunKey, run_key: AppliedRunKey) -> bool:
    return (
        last.observation_time == run_key.observation_time
        and last.resolution_grade == run_key.resolution_grade
    )


def layout_or_postprocess_differs(last: Any, run_key: AppliedRunKey) -> bool:
    """同观测与档位，修边/色带/台风/定位任一不同。"""
    last_key = AppliedRunKey.from_raw(last)
    if last_key is None:
        return False
    return obs_grade_match(last_key, run_key) and last_key != run_key


def provisional_run_key_from_last(
    last: Any,
    *,
    resolution_grade: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool,
    show_typhoon_marker: bool,
    show_my_location: bool = False,
) -> AppliedRunKey | None:
    """用上次指纹的观测时间 + 当前成图参数拼临时指纹（不访问网络）。"""
    last_key = AppliedRunKey.from_raw(last)
    if last_key is None:
        return None
    return AppliedRunKey(
        last_key.observation_time,
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
        bool(reduce_banding),
        bool(show_typhoon_marker),
        bool(show_my_location),
    )


def store_typhoon_center_cache(
    applied_run_state: AppliedRunState | None,
    observation_time: str,
    lat: float,
    lon: float,
) -> None:
    if applied_run_state is None:
        return
    applied_run_state["typhoon_center_cache"] = {
        "observation_time": observation_time,
        "lat": float(lat),
        "lon": float(lon),
    }


def cached_typhoon_center(
    applied_run_state: AppliedRunState | None,
    observation_time: str,
) -> tuple[float, float] | None:
    """仅当缓存观测时间与当前一致时返回 ``(lat, lon)``。"""
    if applied_run_state is None:
        return None
    raw = applied_run_state.get("typhoon_center_cache")
    if not isinstance(raw, dict):
        return None
    obs = raw.get("observation_time")
    lat = raw.get("lat")
    lon = raw.get("lon")
    if obs != observation_time:
        return None
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    return float(lat), float(lon)


def draw_typhoon_marker_at(
    *,
    wallpaper_path: Path,
    pic_side: int,
    lat: float,
    lon: float,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    label: str = "TY",
    color: tuple[int, int, int] = (241, 166, 39),
) -> bool:
    """按经纬度在壁纸上画标记；成功返回 True。"""
    xy = latlon_to_himawari_fd_xy(lat, lon, pic_side)
    if xy is None:
        logging.info("Marker projects outside full-disk frame; skipping")
        return False
    draw_xy = xy
    if auto_adjust:
        try:
            with Image.open(wallpaper_path) as img:
                canvas_w, canvas_h = img.size
        except OSError:
            logging.exception("Failed to open wallpaper for marker offset: %s", wallpaper_path)
            return False
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
    return draw_typhoon_marker(wallpaper_path, draw_xy, label=label, color=color)


def apply_typhoon_marker_if_needed(
    *,
    wallpaper_path: Path,
    pic_side: int,
    observation_time: struct_time,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    fetch_typhoon_center_fn: FetchTyphoonCenter,
    applied_run_state: AppliedRunState | None = None,
) -> None:
    """拉取台风中心、写入对应该观测时间的缓存并标注；失败只记日志。"""
    center = fetch_typhoon_center_fn(observation_time)
    if center is None:
        return
    lat, lon = center
    obs_str = strftime(_OBS_TIME_FMT, observation_time)
    store_typhoon_center_cache(applied_run_state, obs_str, lat, lon)
    draw_typhoon_marker_at(
        wallpaper_path=wallpaper_path,
        pic_side=pic_side,
        lat=lat,
        lon=lon,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
    )


def store_my_location_cache(
    applied_run_state: AppliedRunState | None,
    lat: float,
    lon: float,
    *,
    fetched_at: float | None = None,
) -> None:
    if applied_run_state is None:
        return
    applied_run_state["my_location_cache"] = {
        "lat": float(lat),
        "lon": float(lon),
        "fetched_at": float(time.time() if fetched_at is None else fetched_at),
    }


def cached_my_location(
    applied_run_state: AppliedRunState | None,
    *,
    now: float | None = None,
    ttl_sec: float = _MY_LOCATION_CACHE_TTL_SEC,
) -> tuple[float, float] | None:
    """缓存未过期时返回 ``(lat, lon)``。"""
    if applied_run_state is None:
        return None
    raw = applied_run_state.get("my_location_cache")
    if not isinstance(raw, dict):
        return None
    lat = raw.get("lat")
    lon = raw.get("lon")
    fetched_at = raw.get("fetched_at")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    if not isinstance(fetched_at, (int, float)):
        return None
    clock = time.time() if now is None else now
    if clock - float(fetched_at) > ttl_sec:
        return None
    return float(lat), float(lon)


def apply_my_location_marker_if_needed(
    *,
    wallpaper_path: Path,
    pic_side: int,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    fetch_ip_latlon_fn: FetchIpLatlon,
    applied_run_state: AppliedRunState | None = None,
    allow_network: bool = True,
) -> None:
    """用缓存或 IP 粗定位在壁纸上画「我」标记；失败只记日志。

    Args:
        allow_network: 为 False 时仅使用未过期缓存；为 True 时缓存缺失/过期可联网。
    """
    center = cached_my_location(applied_run_state)
    if center is None and allow_network:
        center = fetch_ip_latlon_fn()
        if center is not None:
            store_my_location_cache(applied_run_state, center[0], center[1])
    if center is None:
        if not allow_network:
            logging.info("Postprocess fast path: no my-location cache; marker not drawn")
        return
    lat, lon = center
    draw_typhoon_marker_at(
        wallpaper_path=wallpaper_path,
        pic_side=pic_side,
        lat=lat,
        lon=lon,
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
        label=_MY_LOCATION_MARKER_LABEL,
        color=_MY_LOCATION_MARKER_COLOR,
    )


def _overlay_typhoon_from_cache(
    *,
    applied_run_state: AppliedRunState,
    wallpaper_path: Path,
    pic_side: int,
    observation_time: str,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
) -> None:
    cached = cached_typhoon_center(applied_run_state, observation_time)
    if cached is None:
        logging.info(
            "Postprocess fast path: no typhoon center cache for %s; marker not drawn",
            observation_time,
        )
        return
    draw_typhoon_marker_at(
        wallpaper_path=wallpaper_path,
        pic_side=pic_side,
        lat=cached[0],
        lon=cached[1],
        auto_adjust=auto_adjust,
        margin_top_percent=margin_top_percent,
        margin_bottom_percent=margin_bottom_percent,
    )
    logging.info(
        "Postprocess fast path: typhoon marker overlaid from cache for %s",
        observation_time,
    )


def _rebuild_from_base(
    *,
    applied_run_state: AppliedRunState,
    last: AppliedRunKey,
    last_wallpaper: Path,
    wallpaper_path: Path,
    reduce_banding: bool,
) -> Path | None:
    """布局未变：从 ``*_base`` 重建成品（可从无标记成品回填 base）。"""
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
        apply_deband_to_file(base, wallpaper_path)
    else:
        shutil.copy2(base, wallpaper_path)
    return base


def _rebuild_from_disk(
    *,
    disk: Path,
    wallpaper_path: Path,
    pic_side: int,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool,
) -> Path | None:
    """边距/修边变了：从 ``*_disk`` 再修边，写入新 base，可选去色带。"""
    if not disk.is_file():
        logging.info("Postprocess fast path skipped: equal disk missing (%s)", disk)
        return None
    wallpaper_path.parent.mkdir(parents=True, exist_ok=True)
    if auto_adjust:
        apply_margins(
            str(disk),
            pic_side,
            str(wallpaper_path),
            top_percent=margin_top_percent,
            bottom_percent=margin_bottom_percent,
            deband=False,
        )
    else:
        shutil.copy2(disk, wallpaper_path)
    base = save_unmarked_base(wallpaper_path)
    if reduce_banding:
        apply_deband_to_file(base, wallpaper_path)
    return base


def try_postprocess_fast_path(
    *,
    applied_run_state: AppliedRunState,
    run_key: AppliedRunKey,
    auto_adjust: bool,
    margin_top_percent: float,
    margin_bottom_percent: float,
    reduce_banding: bool,
    show_typhoon_marker: bool,
    show_my_location: bool = False,
    set_desktop: SetWallpaper,
    record_run_key: bool,
    fetch_ip_latlon_fn: FetchIpLatlon | None = None,
) -> str | None:
    """同观测/档位下仅修边或色带/台风/定位变化时：从 disk/base 重建成品（不拉 latest、不下载）。

    Returns:
        成功时返回观测时间字符串；无法走快路径时 ``None``（调用方应继续全量）。
    """
    last = AppliedRunKey.from_raw(applied_run_state.get("last"))
    if last is None or not layout_or_postprocess_differs(last, run_key):
        return None

    last_path_raw = applied_run_state.get("wallpaper_path")
    if not isinstance(last_path_raw, str) or not last_path_raw.strip():
        return None
    last_wallpaper = Path(last_path_raw.strip())
    layout_same = last.layout == run_key.layout
    observation_time = run_key.observation_time
    pic_side = grade_to_pixel(run_key.resolution_grade)
    disk = resolve_disk_path(applied_run_state, last_wallpaper)
    equal_path = equal_path_from_disk(disk)
    wallpaper_path = (
        last_wallpaper
        if layout_same
        else wallpaper_output_path(equal_path, auto_adjust=auto_adjust)
    )

    try:
        if layout_same:
            # 同布局：复用 *_base（色带/台风/定位开关变化）。
            base = _rebuild_from_base(
                applied_run_state=applied_run_state,
                last=last,
                last_wallpaper=last_wallpaper,
                wallpaper_path=wallpaper_path,
                reduce_banding=reduce_banding,
            )
        else:
            # 修边/边距变了：从 *_disk 重建。
            base = _rebuild_from_disk(
                disk=disk,
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                auto_adjust=auto_adjust,
                margin_top_percent=margin_top_percent,
                margin_bottom_percent=margin_bottom_percent,
                reduce_banding=reduce_banding,
            )
        if base is None:
            return None

        if show_typhoon_marker:
            _overlay_typhoon_from_cache(
                applied_run_state=applied_run_state,
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                observation_time=observation_time,
                auto_adjust=auto_adjust,
                margin_top_percent=margin_top_percent,
                margin_bottom_percent=margin_bottom_percent,
            )
        if show_my_location:
            # IP 定位与观测时间无关：快路径无缓存时允许联网，避免首次开启永远不画。
            apply_my_location_marker_if_needed(
                wallpaper_path=wallpaper_path,
                pic_side=pic_side,
                auto_adjust=auto_adjust,
                margin_top_percent=margin_top_percent,
                margin_bottom_percent=margin_bottom_percent,
                fetch_ip_latlon_fn=fetch_ip_latlon_fn or (lambda: None),
                applied_run_state=applied_run_state,
                allow_network=True,
            )
        logging.info(
            "Postprocess fast path: rebuilt wallpaper "
            "(layout_same=%s banding=%s typhoon=%s my_location=%s)",
            layout_same,
            reduce_banding,
            show_typhoon_marker,
            show_my_location,
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
