"""组装壁纸更新任务：在 assembly 冻结分辨率档位与修边开关。"""

from __future__ import annotations

from collections.abc import Callable

from src.wallpaper_pipeline import run_wallpaper_pipeline


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
