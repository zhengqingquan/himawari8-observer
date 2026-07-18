"""组装壁纸更新任务：在 assembly 冻结分辨率档位与修边开关；运行中可替换档位。"""

from __future__ import annotations

import threading
from collections.abc import Callable

from src.resolution_grade import grade_to_pixel, pixel_to_grade
from src.wallpaper_pipeline import run_wallpaper_pipeline

BuildJob = Callable[..., Callable[[], None]]


def build_wallpaper_job(
    resolution_grade: str,
    *,
    auto_adjust: bool = False,
    run_pipeline: Callable[..., None] | None = None,
) -> Callable[[], None]:
    """返回零参 callable；每次调用使用构造时冻结的 grade / auto_adjust。"""
    pipeline = run_pipeline or run_wallpaper_pipeline

    def job() -> None:
        pipeline(resolution_grade=resolution_grade, auto_adjust=auto_adjust)

    return job


class WallpaperJobRef:
    """托盘与定时器共享的可调用任务；可在运行中更换分辨率档位。"""

    def __init__(
        self,
        resolution_grade: str,
        *,
        auto_adjust: bool = False,
        build_job: BuildJob | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._auto_adjust = auto_adjust
        self._build_job = build_job or build_wallpaper_job
        self._grade = resolution_grade
        self._job = self._build_job(resolution_grade, auto_adjust=auto_adjust)

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

    def set_resolution_grade(self, resolution_grade: str) -> None:
        with self._lock:
            self._grade = resolution_grade
            self._job = self._build_job(resolution_grade, auto_adjust=self._auto_adjust)

    def set_pixel_side(self, pixel_side: int) -> None:
        self.set_resolution_grade(pixel_to_grade(pixel_side))
