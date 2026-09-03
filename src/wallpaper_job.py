"""组装壁纸更新任务：在 assembly 冻结分辨率档位、修边、边距与清理开关；运行中可替换。"""

from __future__ import annotations

import threading
from collections.abc import Callable

from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)
from src.resolution_grade import grade_to_pixel, pixel_to_grade
from src.wallpaper_pipeline import run_wallpaper_pipeline

BuildJob = Callable[..., Callable[[], None]]


def build_wallpaper_job(
    resolution_grade: str,
    *,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    cleanup_after_apply: bool = True,
    run_pipeline: Callable[..., None] | None = None,
) -> Callable[[], None]:
    """返回零参 callable；每次调用使用构造时冻结的参数。"""
    pipeline = run_pipeline or run_wallpaper_pipeline

    def job() -> None:
        pipeline(
            resolution_grade=resolution_grade,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            cleanup_after_apply=cleanup_after_apply,
        )

    return job


class WallpaperJobRef:
    """托盘与定时器共享的可调用任务；可在运行中更换分辨率档位。"""

    def __init__(
        self,
        resolution_grade: str,
        *,
        auto_adjust: bool = False,
        margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
        margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
        cleanup_after_apply: bool = True,
        build_job: BuildJob | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._auto_adjust = auto_adjust
        self._margin_top_percent = margin_top_percent
        self._margin_bottom_percent = margin_bottom_percent
        self._cleanup_after_apply = cleanup_after_apply
        self._build_job = build_job or build_wallpaper_job
        self._grade = resolution_grade
        self._job = self._build_job(
            resolution_grade,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            cleanup_after_apply=cleanup_after_apply,
        )

    def __call__(self) -> None:
        with self._lock:
            job = self._job
        job()

    @property
    def resolution_grade(self) -> str:
        with self._lock:
            return self._grade

    @property
    def pixel_side(self) -> int:
        return grade_to_pixel(self.resolution_grade)

    @property
    def auto_adjust(self) -> bool:
        return self._auto_adjust

    @property
    def margin_top_percent(self) -> float:
        return self._margin_top_percent

    @property
    def margin_bottom_percent(self) -> float:
        return self._margin_bottom_percent

    @property
    def cleanup_after_apply(self) -> bool:
        return self._cleanup_after_apply

    def set_resolution_grade(self, resolution_grade: str) -> None:
        with self._lock:
            self._grade = resolution_grade
            self._rebuild_job_locked()

    def set_pixel_side(self, pixel_side: int) -> None:
        self.set_resolution_grade(pixel_to_grade(pixel_side))

    def set_auto_adjust(self, auto_adjust: bool) -> None:
        with self._lock:
            self._auto_adjust = auto_adjust
            self._rebuild_job_locked()

    def set_margin_top_percent(self, percent: float) -> None:
        with self._lock:
            self._margin_top_percent = percent
            self._rebuild_job_locked()

    def set_margin_bottom_percent(self, percent: float) -> None:
        with self._lock:
            self._margin_bottom_percent = percent
            self._rebuild_job_locked()

    def set_cleanup_after_apply(self, cleanup_after_apply: bool) -> None:
        with self._lock:
            self._cleanup_after_apply = cleanup_after_apply
            self._rebuild_job_locked()

    def _rebuild_job_locked(self) -> None:
        self._job = self._build_job(
            self._grade,
            auto_adjust=self._auto_adjust,
            margin_top_percent=self._margin_top_percent,
            margin_bottom_percent=self._margin_bottom_percent,
            cleanup_after_apply=self._cleanup_after_apply,
        )
