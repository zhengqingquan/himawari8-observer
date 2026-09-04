"""一次性入口：从 Config 读参数并执行一次壁纸更新。

与常驻进程共用 settings 指纹：参数未变且桌面仍是上次成品时可跳过下载。
成功上墙后写回 ``settings.json``（经 ``WallpaperJobRef``）。

常驻进程请用 ``run.py`` → ``src.app.main``。
"""

from __future__ import annotations

from src.cli.args import Config
from src.log import init_logging
from src.settings import applied_run_state_from_settings, load_settings
from src.wallpaper.job import WallpaperJobRef, job_kwargs_from_config


def main() -> None:
    """读取 CLI 配置并同步跑完一轮壁纸流水线。"""
    config = Config()
    init_logging(enabled=config.is_logging_enabled())
    config.log_resolved()
    applied_state = applied_run_state_from_settings(load_settings())
    WallpaperJobRef(
        **job_kwargs_from_config(config),
        applied_run_state=applied_state,
    )()


if __name__ == "__main__":
    main()
