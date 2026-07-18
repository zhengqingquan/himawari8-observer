"""组装壁纸更新任务：在 assembly 冻结分辨率档位。"""

from __future__ import annotations

from collections.abc import Callable

from src.wallpaper_pipeline import run_wallpaper_pipeline


def build_wallpaper_job(
    resolution_grade: str,
    *,
    run_pipeline: Callable[..., None] | None = None,
) -> Callable[[], None]:
    """返回零参 callable；每次调用使用构造时冻结的 resolution_grade。"""
    pipeline = run_pipeline or run_wallpaper_pipeline

    def job() -> None:
        pipeline(resolution_grade=resolution_grade)

    return job
