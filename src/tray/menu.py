"""系统托盘菜单：壁纸时间、分辨率、修边、暂停、开机启动、日志与关于。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

import pystray

from src.log import is_logging_enabled
from src.metadata.app_config import (
    DOWNLOAD_INTERVAL_MINUTES_CHOICES,
    IMAGE_RESOLUTION,
    MARGIN_PERCENT_CHOICES,
)
from src.metadata.app_info import PROGRAM_NAME
from src.startup import is_startup_set
from src.tray.actions import (
    create_image,
    format_observation_local_time,
    format_tray_icon_title,
    on_check_update,
    on_clicked,
    on_open_github,
    on_open_log,
    on_open_program_dir,
    on_quit,
    on_startup,
    on_toggle_logging,
    persist_job_settings,
)
from src.wallpaper.job import WallpaperJobRef
from src.wallpaper.update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)


def _run_wallpaper_update_async(
    job_ref: WallpaperJobRef,
    *,
    progressive: bool = False,
) -> None:
    """在守护线程中触发壁纸更新（不尊重暂停）。"""
    threading.Thread(
        target=lambda: run_wallpaper_update(
            pipeline=job_ref,
            respect_pause=False,
            progressive=progressive,
        ),
        daemon=True,
    ).start()


def setup_tray_icon(job_ref: WallpaperJobRef):
    """创建并阻塞运行系统托盘图标。

    Args:
        job_ref: 托盘与定时器共享的壁纸任务引用，由 ``src.app`` 注入。
    """

    global icon
    icon = pystray.Icon(f"{PROGRAM_NAME}_tray_icon")
    icon.icon = create_image()

    def refresh_tray_title() -> None:
        """任意线程可调用：只更新悬停标题。

        勿在壁纸工作线程调用 ``update_menu``：菜单打开时会卡死 Win32 托盘。
        """
        icon.title = format_tray_icon_title(
            job_ref.applied_observation_time,
            pixel_side=job_ref.applied_pixel_side,
        )

    def refresh_tray_menu() -> None:
        """仅托盘回调线程调用：刷新标题并重建菜单勾选/文案。"""
        refresh_tray_title()
        icon.update_menu()

    def on_update_wallpaper(_icon, _item):
        _run_wallpaper_update_async(job_ref, progressive=True)

    def on_toggle_pause(_icon, _item):
        if is_paused():
            resume()
        else:
            pause()
        refresh_tray_menu()

    def make_interval_item(minutes: int):
        def on_select(_icon, _item):
            job_ref.set_download_interval_minutes(minutes)
            persist_job_settings(job_ref)
            logging.info("Download interval set to %s minutes", minutes)
            refresh_tray_menu()

        return pystray.MenuItem(
            f"每 {minutes} 分钟",
            on_select,
            checked=lambda item: (
                not is_paused() and job_ref.download_interval_minutes == minutes
            ),
            radio=True,
        )

    def make_bool_toggle(
        *,
        get_value: Callable[[], bool],
        set_value: Callable[[bool], None],
        log_label: str,
        trigger_update: bool = True,
    ):
        def on_toggle(_icon, _item):
            enabled = not get_value()
            set_value(enabled)
            persist_job_settings(job_ref)
            logging.info("%s %s", log_label, "enabled" if enabled else "disabled")
            refresh_tray_menu()
            if trigger_update:
                _run_wallpaper_update_async(job_ref)

        return on_toggle

    def make_resolution_item(pixel_side: int):
        def on_select(_icon, _item):
            job_ref.set_pixel_side(pixel_side)
            persist_job_settings(job_ref)
            logging.info(
                "Resolution set to %spx (grade %s)",
                pixel_side,
                job_ref.resolution_grade,
            )
            refresh_tray_menu()
            _run_wallpaper_update_async(job_ref)

        return pystray.MenuItem(
            f"分辨率 {pixel_side}",
            on_select,
            checked=lambda item: job_ref.pixel_side == pixel_side,
            radio=True,
        )

    def make_margin_item(
        *,
        label: str,
        percent: float,
        get_value: Callable[[], float],
        set_value: Callable[[float], None],
        log_label: str,
    ):
        def on_select(_icon, _item):
            set_value(percent)
            persist_job_settings(job_ref)
            logging.info("%s set to %s%%", log_label, percent)
            refresh_tray_menu()
            _run_wallpaper_update_async(job_ref)

        return pystray.MenuItem(
            f"{label} {percent:g}%",
            on_select,
            checked=lambda item: get_value() == percent,
            radio=True,
        )

    on_toggle_adjust = make_bool_toggle(
        get_value=lambda: job_ref.auto_adjust,
        set_value=job_ref.set_auto_adjust,
        log_label="Margin adjust",
    )
    on_toggle_cleanup = make_bool_toggle(
        get_value=lambda: job_ref.cleanup_after_apply,
        set_value=job_ref.set_cleanup_after_apply,
        log_label="Cleanup after apply",
        trigger_update=False,
    )
    on_toggle_use_yesterday_local_time = make_bool_toggle(
        get_value=lambda: job_ref.use_yesterday_local_time,
        set_value=job_ref.set_use_yesterday_local_time,
        log_label="Use yesterday local time",
    )
    on_toggle_reduce_banding = make_bool_toggle(
        get_value=lambda: job_ref.reduce_banding,
        set_value=job_ref.set_reduce_banding,
        log_label="Reduce banding",
    )
    on_toggle_show_typhoon_marker = make_bool_toggle(
        get_value=lambda: job_ref.show_typhoon_marker,
        set_value=job_ref.set_show_typhoon_marker,
        log_label="Show typhoon marker",
    )
    on_toggle_show_my_location = make_bool_toggle(
        get_value=lambda: job_ref.show_my_location,
        set_value=job_ref.set_show_my_location,
        log_label="Show my location",
    )
    on_toggle_show_subsolar_point = make_bool_toggle(
        get_value=lambda: job_ref.show_subsolar_point,
        set_value=job_ref.set_show_subsolar_point,
        log_label="Show subsolar point",
    )
    on_toggle_show_sunglint_point = make_bool_toggle(
        get_value=lambda: job_ref.show_sunglint_point,
        set_value=job_ref.set_show_sunglint_point,
        log_label="Show sunglint point",
    )

    resolution_menu = pystray.Menu(*[make_resolution_item(res) for res in IMAGE_RESOLUTION])
    schedule_menu = pystray.Menu(
        pystray.MenuItem(
            "暂停定时更新",
            on_toggle_pause,
            checked=lambda item: is_paused(),
        ),
        pystray.Menu.SEPARATOR,
        *[make_interval_item(minutes) for minutes in DOWNLOAD_INTERVAL_MINUTES_CHOICES],
    )
    margin_menu = pystray.Menu(
        pystray.MenuItem(
            "启用黑边修边",
            on_toggle_adjust,
            checked=lambda item: job_ref.auto_adjust,
        ),
        pystray.Menu.SEPARATOR,
        *[
            make_margin_item(
                label="顶边",
                percent=p,
                get_value=lambda: job_ref.margin_top_percent,
                set_value=job_ref.set_margin_top_percent,
                log_label="Top margin",
            )
            for p in MARGIN_PERCENT_CHOICES
        ],
        pystray.Menu.SEPARATOR,
        *[
            make_margin_item(
                label="底边",
                percent=p,
                get_value=lambda: job_ref.margin_bottom_percent,
                set_value=job_ref.set_margin_bottom_percent,
                log_label="Bottom margin",
            )
            for p in MARGIN_PERCENT_CHOICES
        ],
    )
    def on_startup_and_refresh(icon_arg, item):
        on_startup(icon_arg, item)
        refresh_tray_menu()

    def on_toggle_logging_and_refresh(icon_arg, item):
        on_toggle_logging(icon_arg, item)
        refresh_tray_menu()

    log_menu = pystray.Menu(
        pystray.MenuItem(
            "启用日志",
            on_toggle_logging_and_refresh,
            checked=lambda item: is_logging_enabled(),
        ),
        pystray.MenuItem("打开日志文件", on_open_log),
    )
    about_menu = pystray.Menu(
        pystray.MenuItem("打开程序所在目录", on_open_program_dir),
        pystray.MenuItem("GitHub", on_open_github),
        pystray.MenuItem(f"关于 {PROGRAM_NAME}", on_clicked),
        pystray.MenuItem("检查更新", on_check_update),
    )

    def wallpaper_time_local_text(_item):
        obs_time = job_ref.applied_observation_time
        if not obs_time:
            return "壁纸时间（本地）：尚未应用"
        try:
            local = format_observation_local_time(obs_time)
        except (ValueError, OSError):
            logging.exception("Failed to convert observation time to local: %s", obs_time)
            return "壁纸时间（本地）：—"
        return f"壁纸时间（本地）：{local}"

    def wallpaper_time_utc_text(_item):
        obs_time = job_ref.applied_observation_time
        if obs_time:
            return f"壁纸时间（UTC）：{obs_time}"
        return "壁纸时间（UTC）：尚未应用"

    icon.menu = pystray.Menu(
        pystray.MenuItem(wallpaper_time_local_text, None),
        pystray.MenuItem(wallpaper_time_utc_text, None),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("立即更新壁纸", on_update_wallpaper),
        pystray.MenuItem("定时更新", schedule_menu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("图片分辨率", resolution_menu),
        pystray.MenuItem("黑边修边", margin_menu),
        pystray.MenuItem(
            "自动清理图片缓存",
            on_toggle_cleanup,
            checked=lambda item: job_ref.cleanup_after_apply,
        ),
        pystray.MenuItem(
            "按本地钟点使用昨日影像",
            on_toggle_use_yesterday_local_time,
            checked=lambda item: job_ref.use_yesterday_local_time,
        ),
        pystray.MenuItem(
            "减轻色带",
            on_toggle_reduce_banding,
            checked=lambda item: job_ref.reduce_banding,
        ),
        pystray.MenuItem(
            "显示台风位置",
            on_toggle_show_typhoon_marker,
            checked=lambda item: job_ref.show_typhoon_marker,
        ),
        pystray.MenuItem(
            "显示我的位置",
            on_toggle_show_my_location,
            checked=lambda item: job_ref.show_my_location,
        ),
        pystray.MenuItem(
            "显示太阳直射点",
            on_toggle_show_subsolar_point,
            checked=lambda item: job_ref.show_subsolar_point,
        ),
        pystray.MenuItem(
            "显示海面耀斑",
            on_toggle_show_sunglint_point,
            checked=lambda item: job_ref.show_sunglint_point,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "开机启动",
            on_startup_and_refresh,
            checked=lambda item: is_startup_set(),
        ),
        pystray.MenuItem("日志", log_menu),
        pystray.MenuItem("关于", about_menu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_quit),
    )

    # 后台上墙只改悬停标题；菜单重建仅在托盘点击回调里做。
    job_ref.set_on_applied(refresh_tray_title)
    refresh_tray_menu()
    icon.run_detached()
