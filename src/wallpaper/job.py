"""组装壁纸更新任务：在 assembly 冻结分辨率档位、修边、边距与清理开关；运行中可替换。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
)
from src.resolution_grade import (
    PROGRESSIVE_PREVIEW_PIXEL,
    grade_to_pixel,
    pixel_to_grade,
    progressive_preview_grade,
)
from src.settings import persist_applied_run_state
from src.wallpaper.pipeline import run_wallpaper_pipeline

BuildJob = Callable[..., Callable[[], None]]
RunPipeline = Callable[..., str | None]


def build_wallpaper_job(
    resolution_grade: str,
    *,
    auto_adjust: bool = False,
    margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
    margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
    cleanup_after_apply: bool = True,
    use_yesterday_local_time: bool = False,
    reduce_banding: bool = False,
    base_dir: Path | None = None,
    run_pipeline: RunPipeline | None = None,
    applied_run_state: dict[str, Any] | None = None,
) -> Callable[[], None]:
    """返回零参 callable；每次调用使用构造时冻结的参数。

    同一 job 闭包内记住上次成功应用的指纹；观测时间与成图参数未变则跳过下载。
    换档 / 改修边等会重建 job，从而清空指纹并强制再跑一轮。
    """
    pipeline = run_pipeline or run_wallpaper_pipeline
    state = (
        applied_run_state
        if applied_run_state is not None
        else {"last": None, "wallpaper_path": None}
    )

    def job() -> None:
        pipeline(
            resolution_grade=resolution_grade,
            auto_adjust=auto_adjust,
            margin_top_percent=margin_top_percent,
            margin_bottom_percent=margin_bottom_percent,
            cleanup_after_apply=cleanup_after_apply,
            use_yesterday_local_time=use_yesterday_local_time,
            reduce_banding=reduce_banding,
            base_dir=base_dir,
            applied_run_state=state,
        )

    return job


class WallpaperJobRef:
    """托盘与定时器共享的可调用任务；可在运行中更换分辨率档位。

    tray / scheduler 只应依赖本引用与 wallpaper.update，勿直连 pipeline / download。
    """

    def __init__(
        self,
        resolution_grade: str,
        *,
        auto_adjust: bool = False,
        margin_top_percent: float = DEFAULT_MARGIN_TOP_PERCENT,
        margin_bottom_percent: float = DEFAULT_MARGIN_BOTTOM_PERCENT,
        cleanup_after_apply: bool = True,
        use_yesterday_local_time: bool = False,
        reduce_banding: bool = False,
        base_dir: Path | None = None,
        build_job: BuildJob | None = None,
        run_pipeline: RunPipeline | None = None,
        applied_run_state: dict[str, Any] | None = None,
        persist_state: bool = True,
    ) -> None:
        self._lock = threading.Lock()
        self._auto_adjust = auto_adjust
        self._margin_top_percent = margin_top_percent
        self._margin_bottom_percent = margin_bottom_percent
        self._cleanup_after_apply = cleanup_after_apply
        self._use_yesterday_local_time = use_yesterday_local_time
        self._reduce_banding = reduce_banding
        self._base_dir = base_dir
        self._build_job = build_job or build_wallpaper_job
        self._run_pipeline = run_pipeline or run_wallpaper_pipeline
        self._grade = resolution_grade
        self._persist_state = persist_state
        self._applied_run_state: dict[str, Any] = (
            dict(applied_run_state)
            if applied_run_state is not None
            else {"last": None, "wallpaper_path": None}
        )
        if "wallpaper_path" not in self._applied_run_state:
            self._applied_run_state["wallpaper_path"] = None
        # 上次成功上墙的观测时间与档位；换参重建 job 清空指纹时仍保留，供托盘展示。
        self._last_observation_time: str | None = None
        self._last_applied_grade: str | None = None
        last = self._applied_run_state.get("last")
        if isinstance(last, tuple) and last:
            self._last_observation_time = str(last[0])
            if len(last) > 1:
                self._last_applied_grade = str(last[1])
        applied_grade = self._applied_run_state.get("applied_grade")
        if isinstance(applied_grade, str) and applied_grade:
            self._last_applied_grade = applied_grade
        self._on_applied: Callable[[], None] | None = None
        self._job = self._build_initial_job()

    def _build_initial_job(self) -> Callable[[], None]:
        return self._build_job(
            self._grade,
            auto_adjust=self._auto_adjust,
            margin_top_percent=self._margin_top_percent,
            margin_bottom_percent=self._margin_bottom_percent,
            cleanup_after_apply=self._cleanup_after_apply,
            use_yesterday_local_time=self._use_yesterday_local_time,
            reduce_banding=self._reduce_banding,
            base_dir=self._base_dir,
            run_pipeline=self._run_pipeline,
            applied_run_state=self._applied_run_state,
        )

    def _persist_applied_state_unlocked(self) -> None:
        if not self._persist_state:
            return
        persist_applied_run_state(self._applied_run_state)

    def set_on_applied(self, callback: Callable[[], None] | None) -> None:
        """注册本轮流水线正常结束后的回调（锁外调用；供托盘刷新悬停标题等）。"""
        with self._lock:
            self._on_applied = callback

    def _notify_applied(self) -> None:
        with self._lock:
            callback = self._on_applied
        if callback is None:
            return
        try:
            callback()
        except Exception:
            logging.exception("WallpaperJobRef on_applied callback failed")

    def __call__(self) -> None:
        with self._lock:
            job = self._job
        job()
        with self._lock:
            self._persist_applied_state_unlocked()
        self._notify_applied()

    def run_progressive(
        self,
        preview_pixel: int = PROGRESSIVE_PREVIEW_PIXEL,
    ) -> None:
        """先预览档上墙再跑目标档（目标边长大于预览时）；否则只跑目标档。

        两轮共用同一 ``applied_run_state``。预览轮不写指纹、不清理；目标轮再落盘。
        预览成功上墙后会刷新展示用观测时间并通知 ``on_applied``（仍不写跳过指纹）。
        """
        with self._lock:
            target_grade = self._grade
            auto_adjust = self._auto_adjust
            margin_top_percent = self._margin_top_percent
            margin_bottom_percent = self._margin_bottom_percent
            cleanup_after_apply = self._cleanup_after_apply
            use_yesterday_local_time = self._use_yesterday_local_time
            reduce_banding = self._reduce_banding
            base_dir = self._base_dir
            state = self._applied_run_state
            pipeline = self._run_pipeline

        common = {
            "auto_adjust": auto_adjust,
            "margin_top_percent": margin_top_percent,
            "margin_bottom_percent": margin_bottom_percent,
            "use_yesterday_local_time": use_yesterday_local_time,
            "reduce_banding": reduce_banding,
            "base_dir": base_dir,
            "applied_run_state": state,
        }
        if grade_to_pixel(target_grade) <= preview_pixel:
            pipeline(
                resolution_grade=target_grade,
                cleanup_after_apply=cleanup_after_apply,
                record_run_key=True,
                **common,
            )
            with self._lock:
                self._persist_applied_state_unlocked()
            self._notify_applied()
            return

        preview_grade = (
            progressive_preview_grade()
            if preview_pixel == PROGRESSIVE_PREVIEW_PIXEL
            else pixel_to_grade(preview_pixel)
        )
        logging.info(
            "Progressive wallpaper: preview %s then target %s",
            preview_grade,
            target_grade,
        )
        preview_obs: str | None = None
        try:
            preview_obs = pipeline(
                resolution_grade=preview_grade,
                cleanup_after_apply=False,
                record_run_key=False,
                **common,
            )
        except Exception:
            logging.exception(
                "Progressive preview failed; continuing to target grade %s",
                target_grade,
            )
        if preview_obs:
            with self._lock:
                self._last_observation_time = preview_obs
            self._notify_applied()
        pipeline(
            resolution_grade=target_grade,
            cleanup_after_apply=cleanup_after_apply,
            record_run_key=True,
            **common,
        )
        with self._lock:
            self._persist_applied_state_unlocked()
        self._notify_applied()

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

    @property
    def use_yesterday_local_time(self) -> bool:
        return self._use_yesterday_local_time

    @property
    def reduce_banding(self) -> bool:
        return self._reduce_banding

    @property
    def base_dir(self) -> Path | None:
        return self._base_dir

    @property
    def applied_observation_time(self) -> str | None:
        """当前壁纸对应的观测时间（``YYYY-MM-DD HH:MM:SS``，UTC）；尚未成功应用则为 ``None``。"""
        with self._lock:
            last = self._applied_run_state.get("last")
            if isinstance(last, tuple) and last:
                self._last_observation_time = str(last[0])
            return self._last_observation_time

    @property
    def applied_resolution_grade(self) -> str | None:
        """当前桌面壁纸对应的分辨率档位；尚未成功应用则为 ``None``。"""
        with self._lock:
            last = self._applied_run_state.get("last")
            if isinstance(last, tuple) and len(last) > 1:
                self._last_applied_grade = str(last[1])
            applied_grade = self._applied_run_state.get("applied_grade")
            if isinstance(applied_grade, str) and applied_grade:
                self._last_applied_grade = applied_grade
            return self._last_applied_grade

    @property
    def applied_pixel_side(self) -> int | None:
        """当前桌面壁纸对应的像素边长；尚未成功应用则为 ``None``。"""
        grade = self.applied_resolution_grade
        if grade is None:
            return None
        return grade_to_pixel(grade)

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

    def set_use_yesterday_local_time(self, use_yesterday_local_time: bool) -> None:
        with self._lock:
            self._use_yesterday_local_time = use_yesterday_local_time
            self._rebuild_job_locked()

    def set_reduce_banding(self, reduce_banding: bool) -> None:
        with self._lock:
            self._reduce_banding = reduce_banding
            self._rebuild_job_locked()

    def _rebuild_job_locked(self) -> None:
        last = self._applied_run_state.get("last")
        if isinstance(last, tuple) and last:
            self._last_observation_time = str(last[0])
            if len(last) > 1:
                self._last_applied_grade = str(last[1])
        applied_grade = self._applied_run_state.get("applied_grade")
        if isinstance(applied_grade, str) and applied_grade:
            self._last_applied_grade = applied_grade
        wallpaper_path = self._applied_run_state.get("wallpaper_path")
        self._applied_run_state = {
            "last": None,
            "wallpaper_path": wallpaper_path,
            "applied_grade": self._last_applied_grade,
        }
        self._job = self._build_job(
            self._grade,
            auto_adjust=self._auto_adjust,
            margin_top_percent=self._margin_top_percent,
            margin_bottom_percent=self._margin_bottom_percent,
            cleanup_after_apply=self._cleanup_after_apply,
            use_yesterday_local_time=self._use_yesterday_local_time,
            reduce_banding=self._reduce_banding,
            base_dir=self._base_dir,
            run_pipeline=self._run_pipeline,
            applied_run_state=self._applied_run_state,
        )
