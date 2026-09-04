"""成图指纹：AppliedRunKey、跳过判定与 applied_run_state 记忆。"""

from __future__ import annotations

from pathlib import Path
from time import strftime, struct_time
from typing import Any, NamedTuple

from src.wallpaper.paths import (
    AppliedRunState,
    path_str,
    wallpaper_base_path,
    wallpaper_disk_path,
)

OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"


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
        strftime(OBS_TIME_FMT, observation_time),
        resolution_grade,
        auto_adjust,
        float(margin_top_percent),
        float(margin_bottom_percent),
        bool(reduce_banding),
        bool(show_typhoon_marker),
        bool(show_my_location),
    )


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
    applied_run_state["wallpaper_path"] = path_str(wallpaper_path)
    base = wallpaper_base if wallpaper_base is not None else wallpaper_base_path(wallpaper_path)
    applied_run_state["wallpaper_base_path"] = path_str(base)
    disk = wallpaper_disk if wallpaper_disk is not None else wallpaper_disk_path(wallpaper_path)
    applied_run_state["wallpaper_disk_path"] = path_str(disk)


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
