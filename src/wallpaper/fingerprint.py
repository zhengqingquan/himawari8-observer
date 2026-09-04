"""成图指纹：AppliedRunKey、跳过判定与 applied_run_state 记忆。"""

from __future__ import annotations

from pathlib import Path
from time import strftime, struct_time
from typing import Any, NamedTuple

from src.metadata.app_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)
from src.wallpaper.paths import (
    AppliedRunState,
    path_str,
    wallpaper_base_path,
    wallpaper_disk_path,
)

OBS_TIME_FMT = "%Y-%m-%d %H:%M:%S"


class PostprocessOptions(NamedTuple):
    """影响成品外观的成图开关（不含观测时间 / 档位；cleanup 另传）。"""

    auto_adjust: bool = False
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT
    reduce_banding: bool = False
    show_typhoon_marker: bool = False
    show_my_location: bool = False

    @property
    def layout(self) -> tuple[bool, float, float]:
        """修边开关与上下边距（与色带/台风/定位无关）。"""
        return (
            self.auto_adjust,
            self.margin_top_percent,
            self.margin_bottom_percent,
        )


class LivePostprocess(NamedTuple):
    """下载过程中可刷新的成图状态（options + cleanup）。"""

    options: PostprocessOptions
    cleanup_after_apply: bool = True


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
        return self.options.layout

    @property
    def options(self) -> PostprocessOptions:
        """指纹中的成图开关部分。"""
        return PostprocessOptions(
            self.auto_adjust,
            self.margin_top_percent,
            self.margin_bottom_percent,
            self.reduce_banding,
            self.show_typhoon_marker,
            self.show_my_location,
        )

    @classmethod
    def from_raw(cls, value: Any) -> AppliedRunKey | None:
        """接受本类型或完整 8 项序列；非法则 ``None``。"""
        if isinstance(value, cls):
            return value
        if not isinstance(value, (tuple, list)) or len(value) != len(cls._fields):
            return None
        try:
            (
                obs_time,
                grade,
                auto_adjust,
                top,
                bottom,
                reduce_banding,
                show_typhoon_marker,
                show_my_location,
            ) = value
            key = cls(
                str(obs_time),
                str(grade),
                bool(auto_adjust),
                float(top),
                float(bottom),
                bool(reduce_banding),
                bool(show_typhoon_marker),
                bool(show_my_location),
            )
        except (TypeError, ValueError):
            return None
        if not key.observation_time or not key.resolution_grade:
            return None
        return key


def build_applied_run_key(
    observation_time: struct_time,
    *,
    resolution_grade: str,
    options: PostprocessOptions,
) -> AppliedRunKey:
    """用于判断是否可跳过重复下载的指纹（观测时间 + 影响成图的参数）。"""
    return AppliedRunKey(
        strftime(OBS_TIME_FMT, observation_time),
        resolution_grade,
        options.auto_adjust,
        float(options.margin_top_percent),
        float(options.margin_bottom_percent),
        bool(options.reduce_banding),
        bool(options.show_typhoon_marker),
        bool(options.show_my_location),
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
    options: PostprocessOptions,
) -> AppliedRunKey | None:
    """用上次指纹的观测时间 + 当前成图参数拼临时指纹（不访问网络）。"""
    last_key = AppliedRunKey.from_raw(last)
    if last_key is None:
        return None
    return AppliedRunKey(
        last_key.observation_time,
        resolution_grade,
        options.auto_adjust,
        float(options.margin_top_percent),
        float(options.margin_bottom_percent),
        bool(options.reduce_banding),
        bool(options.show_typhoon_marker),
        bool(options.show_my_location),
    )
