"""常驻应用启动：日志、CLI、托盘、调度、主线程阻塞。"""

from __future__ import annotations

import logging
import threading

from src.cli.args import Config
from src.event import wait_for_shutdown
from src.log import init_logging
from src.scheduler import start_scheduler
from src.settings import applied_run_state_from_settings, default_settings, load_settings
from src.startup import apply_startup_enabled
from src.tray.menu import setup_tray_icon
from src.wallpaper.job import WallpaperJobRef, job_kwargs_from_config


def main() -> None:
    try:
        config = Config()
        init_logging(enabled=config.is_logging_enabled())
        config.log_resolved()

        file_settings = load_settings()
        startup_enabled = bool(
            {**default_settings(), **file_settings}.get("startup_enabled", False)
        )
        apply_startup_enabled(startup_enabled)
        logging.info("Startup on boot: %s", "enabled" if startup_enabled else "disabled")

        applied_state = applied_run_state_from_settings(file_settings)
        job_ref = WallpaperJobRef(
            **job_kwargs_from_config(config),
            applied_run_state=applied_state,
        )

        # 托盘与调度共享同一任务引用（托盘可运行中换档）
        threading.Thread(target=lambda: setup_tray_icon(job_ref), daemon=True).start()
        threading.Thread(
            target=lambda: start_scheduler(
                job_ref,
                interval_seconds=job_ref.download_interval_minutes * 60,
            ),
            daemon=True,
        ).start()

        wait_for_shutdown()
    except Exception:
        logging.exception("Application failed to start or crashed")
