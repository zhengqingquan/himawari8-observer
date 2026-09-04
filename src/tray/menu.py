"""系统托盘菜单：壁纸时间、分辨率、修边、暂停、开机启动、日志与关于。"""

from __future__ import annotations

import logging
import threading

import pystray

from src.log import is_logging_enabled
from src.metadata.app_config import IMAGE_RESOLUTION, MARGIN_PERCENT_CHOICES
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


def setup_tray_icon(job_ref: WallpaperJobRef):
    """创建并阻塞运行系统托盘图标。

    Args:
        job_ref: 托盘与定时器共享的壁纸任务引用，由 ``src.app`` 注入。
    """

    def on_update_wallpaper(icon, item):
        threading.Thread(
            target=lambda: run_wallpaper_update(
                pipeline=job_ref,
                respect_pause=False,
                progressive=True,
            ),
            daemon=True,
        ).start()

    def on_toggle_pause(icon, item):
        if is_paused():
            resume()
        else:
            pause()

    def make_resolution_item(pixel_side: int):
        def on_select(icon, item):
            job_ref.set_pixel_side(pixel_side)
            persist_job_settings(job_ref)
            logging.info(
                "Resolution set to %spx (grade %s)",
                pixel_side,
                job_ref.resolution_grade,
            )
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"分辨率 {pixel_side}",
            on_select,
            checked=lambda item: job_ref.pixel_side == pixel_side,
            radio=True,
        )

    def on_toggle_adjust(icon, item):
        enabled = not job_ref.auto_adjust
        job_ref.set_auto_adjust(enabled)
        persist_job_settings(job_ref)
        logging.info("Margin adjust %s", "enabled" if enabled else "disabled")
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def on_toggle_cleanup(icon, item):
        enabled = not job_ref.cleanup_after_apply
        job_ref.set_cleanup_after_apply(enabled)
        persist_job_settings(job_ref)
        logging.info("Cleanup after apply %s", "enabled" if enabled else "disabled")

    def on_toggle_use_yesterday_local_time(icon, item):
        enabled = not job_ref.use_yesterday_local_time
        job_ref.set_use_yesterday_local_time(enabled)
        persist_job_settings(job_ref)
        logging.info(
            "Use yesterday local time %s",
            "enabled" if enabled else "disabled",
        )
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def on_toggle_reduce_banding(icon, item):
        enabled = not job_ref.reduce_banding
        job_ref.set_reduce_banding(enabled)
        persist_job_settings(job_ref)
        logging.info("Reduce banding %s", "enabled" if enabled else "disabled")
        threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
            daemon=True,
        ).start()

    def make_margin_top_item(percent: float):
        def on_select(icon, item):
            job_ref.set_margin_top_percent(percent)
            persist_job_settings(job_ref)
            logging.info("Top margin set to %s%%", percent)
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"顶边 {percent:g}%",
            on_select,
            checked=lambda item: job_ref.margin_top_percent == percent,
            radio=True,
        )

    def make_margin_bottom_item(percent: float):
        def on_select(icon, item):
            job_ref.set_margin_bottom_percent(percent)
            persist_job_settings(job_ref)
            logging.info("Bottom margin set to %s%%", percent)
            threading.Thread(
                target=lambda: run_wallpaper_update(pipeline=job_ref, respect_pause=False),
                daemon=True,
            ).start()

        return pystray.MenuItem(
            f"底边 {percent:g}%",
            on_select,
            checked=lambda item: job_ref.margin_bottom_percent == percent,
            radio=True,
        )

    global icon
    icon = pystray.Icon(f"{PROGRAM_NAME}_tray_icon")
    icon.icon = create_image()

    def refresh_tray_display() -> None:
        """刷新悬停标题，并重建菜单（Win32 会缓存，需 update_menu 才能看到新时间）。"""
        icon.title = format_tray_icon_title(
            job_ref.applied_observation_time,
            pixel_side=job_ref.applied_pixel_side,
        )
        icon.update_menu()

    resolution_menu = pystray.Menu(*[make_resolution_item(res) for res in IMAGE_RESOLUTION])
    margin_menu = pystray.Menu(
        pystray.MenuItem(
            "启用黑边修边",
            on_toggle_adjust,
            checked=lambda item: job_ref.auto_adjust,
        ),
        pystray.Menu.SEPARATOR,
        *[make_margin_top_item(p) for p in MARGIN_PERCENT_CHOICES],
        pystray.Menu.SEPARATOR,
        *[make_margin_bottom_item(p) for p in MARGIN_PERCENT_CHOICES],
    )
    log_menu = pystray.Menu(
        pystray.MenuItem(
            "启用日志",
            on_toggle_logging,
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
        pystray.MenuItem(
            "暂停更新壁纸",
            on_toggle_pause,
            checked=lambda item: is_paused(),
        ),
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
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "开机启动",
            on_startup,
            checked=lambda item: is_startup_set(),
        ),
        pystray.MenuItem("日志", log_menu),
        pystray.MenuItem("关于", about_menu),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_quit),
    )

    job_ref.set_on_applied(refresh_tray_display)
    refresh_tray_display()
    icon.run_detached()
