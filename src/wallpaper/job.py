"""组装壁纸更新任务：在 assembly 冻结分辨率档位、修边、边距与清理开关；运行中可替换。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from src.metadata.app_config import (
    DEFAULT_DOWNLOAD_INTERVAL_MINUTES,
    DOWNLOAD_INTERVAL_MINUTES_CHOICES,
)
from src.resolution_grade import (
    PROGRESSIVE_PREVIEW_PIXEL,
    grade_to_pixel,
    pixel_to_grade,
    progressive_preview_grade,
)
from src.scheduler import reschedule_interval
from src.settings import persist_applied_run_state
from src.download.geoip import fetch_ip_latlon
from src.download.jtwc import fetch_jtwc_invests
from src.download.typhoon import fetch_typhoon_center
from src.wallpaper.desktop import get_desktop_wallpaper as read_desktop_wallpaper
from src.wallpaper.desktop import set_wallpaper as apply_desktop_wallpaper
from src.wallpaper.fast_path import try_postprocess_fast_path
from src.wallpaper.fingerprint import (
    AppliedRunKey,
    LivePostprocess,
    PostprocessOptions,
    layout_or_postprocess_differs,
    provisional_run_key_from_last,
)
from src.wallpaper.pipeline import run_wallpaper_pipeline
from src.wallpaper.update import is_paused, resume

BuildJob = Callable[..., Callable[[], None]]
RunPipeline = Callable[..., str | None]


class WallpaperJobConfig(Protocol):
    """Config / 等价对象：提供装配 job 所需的 getter。"""

    def get_download_resolution(self) -> int: ...

    def is_auto_adjust_picture(self) -> bool: ...

    def get_margin_top_percent(self) -> float: ...

    def get_margin_bottom_percent(self) -> float: ...

    def is_cleanup_after_apply(self) -> bool: ...

    def is_use_yesterday_local_time(self) -> bool: ...

    def is_reduce_banding(self) -> bool: ...

    def is_show_typhoon_marker(self) -> bool: ...

    def is_show_my_location(self) -> bool: ...

    def is_show_subsolar_point(self) -> bool: ...

    def get_download_interval_minutes(self) -> int: ...


def job_kwargs_from_config(config: WallpaperJobConfig) -> dict[str, Any]:
    """将 Config getter 映射为 ``WallpaperJobRef`` 的 kwargs。"""
    return {
        "resolution_grade": pixel_to_grade(config.get_download_resolution()),
        "options": PostprocessOptions(
            auto_adjust=config.is_auto_adjust_picture(),
            margin_top_percent=config.get_margin_top_percent(),
            margin_bottom_percent=config.get_margin_bottom_percent(),
            reduce_banding=config.is_reduce_banding(),
            show_typhoon_marker=config.is_show_typhoon_marker(),
            show_my_location=config.is_show_my_location(),
            show_subsolar_point=config.is_show_subsolar_point(),
        ),
        "cleanup_after_apply": config.is_cleanup_after_apply(),
        "use_yesterday_local_time": config.is_use_yesterday_local_time(),
        "download_interval_minutes": config.get_download_interval_minutes(),
    }


def build_wallpaper_job(
    resolution_grade: str,
    *,
    options: PostprocessOptions | None = None,
    cleanup_after_apply: bool = True,
    use_yesterday_local_time: bool = False,
    base_dir: Path | None = None,
    run_pipeline: RunPipeline | None = None,
    applied_run_state: dict[str, Any] | None = None,
    refresh_postprocess: Callable[[], LivePostprocess] | None = None,
) -> Callable[[], None]:
    """返回零参 callable；每次调用使用构造时冻结的参数。

    同一 job 闭包内记住上次成功应用的指纹；观测时间与成图参数未变则跳过下载。
    换档 / 改修边等会重建 job，从而清空指纹并强制再跑一轮。
    ``refresh_postprocess`` 在下载完成后上墙前再读最新成图开关（由 WallpaperJobRef 注入）。
    """
    pipeline = run_pipeline or run_wallpaper_pipeline
    opts = options if options is not None else PostprocessOptions()
    state = (
        applied_run_state
        if applied_run_state is not None
        else {"last": None, "wallpaper_path": None}
    )

    def job() -> None:
        pipeline(
            resolution_grade=resolution_grade,
            options=opts,
            cleanup_after_apply=cleanup_after_apply,
            use_yesterday_local_time=use_yesterday_local_time,
            base_dir=base_dir,
            applied_run_state=state,
            refresh_postprocess=refresh_postprocess,
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
        options: PostprocessOptions | None = None,
        cleanup_after_apply: bool = True,
        use_yesterday_local_time: bool = False,
        download_interval_minutes: int = DEFAULT_DOWNLOAD_INTERVAL_MINUTES,
        base_dir: Path | None = None,
        build_job: BuildJob | None = None,
        run_pipeline: RunPipeline | None = None,
        applied_run_state: dict[str, Any] | None = None,
        persist_state: bool = True,
    ) -> None:
        self._lock = threading.Lock()
        self._live_postprocess_lock = threading.Lock()
        self._options = options if options is not None else PostprocessOptions()
        self._cleanup_after_apply = cleanup_after_apply
        self._use_yesterday_local_time = use_yesterday_local_time
        minutes = int(download_interval_minutes)
        if minutes not in DOWNLOAD_INTERVAL_MINUTES_CHOICES:
            minutes = DEFAULT_DOWNLOAD_INTERVAL_MINUTES
        self._download_interval_minutes = minutes
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
        # 上次成功上墙的观测时间与档位（供托盘展示）；与 applied_run_state 同步。
        self._last_observation_time: str | None = None
        self._last_applied_grade: str | None = None
        self._sync_applied_display_unlocked()
        self._on_applied: Callable[[], None] | None = None
        self._job = self._build_initial_job()

    def _sync_applied_display_unlocked(self) -> None:
        """从 ``applied_run_state`` 回填托盘展示用的观测时间与档位（调用方须已持锁或尚单线程）。"""
        last = AppliedRunKey.from_raw(self._applied_run_state.get("last"))
        if last is not None:
            self._last_observation_time = last.observation_time
            self._last_applied_grade = last.resolution_grade
        applied_grade = self._applied_run_state.get("applied_grade")
        if isinstance(applied_grade, str) and applied_grade:
            self._last_applied_grade = applied_grade

    def _build_initial_job(self) -> Callable[[], None]:
        return self._build_job(
            self._grade,
            options=self._options,
            cleanup_after_apply=self._cleanup_after_apply,
            use_yesterday_local_time=self._use_yesterday_local_time,
            base_dir=self._base_dir,
            run_pipeline=self._run_pipeline,
            applied_run_state=self._applied_run_state,
            refresh_postprocess=self._refresh_postprocess,
        )

    def _persist_applied_state_unlocked(self) -> None:
        if not self._persist_state:
            return
        persist_applied_run_state(self._applied_run_state)

    def _set_and_rebuild(self, attr: str, value: Any) -> None:
        with self._lock:
            setattr(self, attr, value)
            self._rebuild_job_locked()

    def _replace_options(self, **changes: Any) -> None:
        with self._lock:
            self._options = self._options._replace(**changes)
            self._rebuild_job_locked()

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

    def _live_postprocess_unlocked(self) -> LivePostprocess:
        return LivePostprocess(
            options=self._options,
            cleanup_after_apply=self._cleanup_after_apply,
        )

    def _refresh_postprocess(self) -> LivePostprocess:
        with self._lock:
            return self._live_postprocess_unlocked()

    def _run_with_live_postprocess(
        self,
        *,
        resolution_grade: str | None = None,
        cleanup_after_apply: bool | None = None,
        record_run_key: bool = True,
    ) -> str | None:
        with self._lock:
            grade = resolution_grade if resolution_grade is not None else self._grade
            use_yesterday = self._use_yesterday_local_time
            base_dir = self._base_dir
            state = self._applied_run_state
            pipeline = self._run_pipeline
            live = self._live_postprocess_unlocked()
        if cleanup_after_apply is not None:
            live = live._replace(cleanup_after_apply=cleanup_after_apply)
        return pipeline(
            resolution_grade=grade,
            options=live.options,
            cleanup_after_apply=live.cleanup_after_apply,
            use_yesterday_local_time=use_yesterday,
            base_dir=base_dir,
            applied_run_state=state,
            record_run_key=record_run_key,
            refresh_postprocess=self._refresh_postprocess,
        )

    def try_live_postprocess(self) -> bool:
        """Busy 时立刻对已上墙成品做后处理快路径（不占 update 互斥锁）。

        仅当同观测/档位下修边、色带、台风或定位变化且 disk/base 仍可用时成功。

        Returns:
            True 若成功重建并设壁纸；无法走快路径时 False。
        """
        with self._live_postprocess_lock:
            with self._lock:
                state = self._applied_run_state
                grade = self._grade
                options = self._options
                last = state.get("last")

            provisional = provisional_run_key_from_last(
                last,
                resolution_grade=grade,
                options=options,
            )
            if provisional is None or not layout_or_postprocess_differs(last, provisional):
                return False

            obs = try_postprocess_fast_path(
                applied_run_state=state,
                run_key=provisional,
                set_desktop=apply_desktop_wallpaper,
                record_run_key=True,
                fetch_ip_latlon_fn=fetch_ip_latlon,
                fetch_typhoon_center_fn=fetch_typhoon_center,
                fetch_jtwc_invests_fn=fetch_jtwc_invests,
                get_desktop=read_desktop_wallpaper,
            )
            if obs is None:
                return False

            with self._lock:
                self._sync_applied_display_unlocked()
                self._persist_applied_state_unlocked()
            self._notify_applied()
            return True

    def run_progressive(
        self,
        preview_pixel: int = PROGRESSIVE_PREVIEW_PIXEL,
    ) -> None:
        """先预览档上墙再跑目标档（目标边长大于预览时）；否则只跑目标档。

        两轮共用同一 ``applied_run_state``。预览轮不写指纹、不清理；目标轮再落盘。
        预览成功上墙后会刷新展示用观测时间并通知 ``on_applied``（仍不写跳过指纹）。
        每轮上墙前经 ``refresh_postprocess`` 读最新成图开关。
        """
        with self._lock:
            target_grade = self._grade
            cleanup_after_apply = self._cleanup_after_apply

        if grade_to_pixel(target_grade) <= preview_pixel:
            self._run_with_live_postprocess(
                resolution_grade=target_grade,
                cleanup_after_apply=cleanup_after_apply,
                record_run_key=True,
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
            preview_obs = self._run_with_live_postprocess(
                resolution_grade=preview_grade,
                cleanup_after_apply=False,
                record_run_key=False,
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
        self._run_with_live_postprocess(
            resolution_grade=target_grade,
            cleanup_after_apply=cleanup_after_apply,
            record_run_key=True,
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
    def options(self) -> PostprocessOptions:
        with self._lock:
            return self._options

    @property
    def auto_adjust(self) -> bool:
        return self.options.auto_adjust

    @property
    def margin_top_percent(self) -> float:
        return self.options.margin_top_percent

    @property
    def margin_bottom_percent(self) -> float:
        return self.options.margin_bottom_percent

    @property
    def cleanup_after_apply(self) -> bool:
        return self._cleanup_after_apply

    @property
    def use_yesterday_local_time(self) -> bool:
        return self._use_yesterday_local_time

    @property
    def reduce_banding(self) -> bool:
        return self.options.reduce_banding

    @property
    def show_typhoon_marker(self) -> bool:
        return self.options.show_typhoon_marker

    @property
    def show_my_location(self) -> bool:
        return self.options.show_my_location

    @property
    def show_subsolar_point(self) -> bool:
        return self.options.show_subsolar_point

    @property
    def download_interval_minutes(self) -> int:
        with self._lock:
            return self._download_interval_minutes

    @property
    def base_dir(self) -> Path | None:
        return self._base_dir

    @property
    def applied_observation_time(self) -> str | None:
        """当前壁纸对应的观测时间（``YYYY-MM-DD HH:MM:SS``，UTC）；尚未成功应用则为 ``None``。"""
        with self._lock:
            self._sync_applied_display_unlocked()
            return self._last_observation_time

    @property
    def applied_resolution_grade(self) -> str | None:
        """当前桌面壁纸对应的分辨率档位；尚未成功应用则为 ``None``。"""
        with self._lock:
            self._sync_applied_display_unlocked()
            return self._last_applied_grade

    @property
    def applied_pixel_side(self) -> int | None:
        """当前桌面壁纸对应的像素边长；尚未成功应用则为 ``None``。"""
        grade = self.applied_resolution_grade
        if grade is None:
            return None
        return grade_to_pixel(grade)

    def set_resolution_grade(self, resolution_grade: str) -> None:
        self._set_and_rebuild("_grade", resolution_grade)

    def set_pixel_side(self, pixel_side: int) -> None:
        self.set_resolution_grade(pixel_to_grade(pixel_side))

    def set_auto_adjust(self, auto_adjust: bool) -> None:
        self._replace_options(auto_adjust=auto_adjust)

    def set_margin_top_percent(self, percent: float) -> None:
        self._replace_options(margin_top_percent=percent)

    def set_margin_bottom_percent(self, percent: float) -> None:
        self._replace_options(margin_bottom_percent=percent)

    def set_cleanup_after_apply(self, cleanup_after_apply: bool) -> None:
        self._set_and_rebuild("_cleanup_after_apply", cleanup_after_apply)

    def set_use_yesterday_local_time(self, use_yesterday_local_time: bool) -> None:
        self._set_and_rebuild("_use_yesterday_local_time", use_yesterday_local_time)

    def set_reduce_banding(self, reduce_banding: bool) -> None:
        self._replace_options(reduce_banding=reduce_banding)

    def set_show_typhoon_marker(self, show_typhoon_marker: bool) -> None:
        self._replace_options(show_typhoon_marker=show_typhoon_marker)

    def set_show_my_location(self, show_my_location: bool) -> None:
        self._replace_options(show_my_location=show_my_location)

    def set_show_subsolar_point(self, show_subsolar_point: bool) -> None:
        self._replace_options(show_subsolar_point=show_subsolar_point)

    def set_download_interval_minutes(self, minutes: int) -> None:
        """更新调度间隔并 reschedule；若已暂停则顺带 resume。不重建流水线 job。"""
        value = int(minutes)
        if value not in DOWNLOAD_INTERVAL_MINUTES_CHOICES:
            logging.warning("Ignoring invalid download_interval_minutes: %r", minutes)
            return
        with self._lock:
            self._download_interval_minutes = value
        reschedule_interval(value * 60)
        if is_paused():
            resume()

    def _rebuild_job_locked(self) -> None:
        self._sync_applied_display_unlocked()
        # 必须保持同一 dict 引用：进行中的 pipeline 写指纹时与后续 persist 共用这份 state。
        # 若在此 new 一个 dict，当轮完成写到旧对象，persist 读新对象 → 指纹永久停在旧观测时间。
        self._applied_run_state["applied_grade"] = self._last_applied_grade
        self._job = self._build_initial_job()
