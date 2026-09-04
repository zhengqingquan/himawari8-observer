"""CLI 参数解析：单例 Config（默认 → settings.json → 显式 CLI）。"""

from __future__ import annotations

import argparse
import logging

from src.metadata.app_config import IMAGE_RESOLUTION
from src.metadata.app_info import DESCRIPTION, EPILOG, PROGRAM_NAME, SOFTWARE_VERSION
from src.settings import resolve_runtime_settings


def _percent(value: str) -> float:
    """将字符串解析为 0–100 的百分比。"""
    try:
        percent = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid percent: {value!r}") from exc
    if not 0.0 <= percent <= 100.0:
        raise argparse.ArgumentTypeError("percent must be between 0 and 100")
    return percent


class Config:
    """进程内单例：解析 CLI，并与 settings.json 合并为运行时配置。"""

    _instance = None
    _parser = None
    _args = None
    _resolved = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.parse_arguments()
        self._initialized = True

    def parse_arguments(self):
        """定义并解析 CLI；未传选项为 None，再与文件合并。"""
        self._parser = argparse.ArgumentParser(
            prog=PROGRAM_NAME,
            description=DESCRIPTION,
            epilog=EPILOG,
        )

        self._parser.add_argument(
            "-r",
            "--resolution",
            type=int,
            choices=IMAGE_RESOLUTION,
            default=None,
            dest="download_resolution",
            help='"equal" represents how many 550-pixel images one side of an image is equal to.',
        )

        self._parser.add_argument(
            "-a",
            "--adjust",
            dest="is_auto_adjust_picture",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Pad wallpaper with black borders so the taskbar covers the margin "
            "(default: on; use --no-adjust to disable).",
        )

        self._parser.add_argument(
            "--margin-top",
            type=_percent,
            default=None,
            dest="margin_top_percent",
            help="Top black-border percent of the square image side (default: 0).",
        )

        self._parser.add_argument(
            "--margin-bottom",
            type=_percent,
            default=None,
            dest="margin_bottom_percent",
            help="Bottom black-border percent of the square image side (default: 5).",
        )

        self._parser.add_argument(
            "--cleanup-after-apply",
            dest="cleanup_after_apply",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="After setting wallpaper, delete tiles and old img folders "
            "but keep the current wallpaper file (default: on; "
            "use --no-cleanup-after-apply to disable).",
        )

        self._parser.add_argument(
            "--use-yesterday-local-time",
            dest="use_yesterday_local_time",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Use yesterday's image at the same local clock time "
            "(floored to 10 minutes UTC; default: off; "
            "use --use-yesterday-local-time to enable).",
        )

        self._parser.add_argument(
            "--reduce-banding",
            dest="reduce_banding",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Reduce color banding in composed wallpaper "
            "(default: off; use --reduce-banding to enable).",
        )

        self._parser.add_argument(
            "--show-typhoon-marker",
            dest="show_typhoon_marker",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Mark typhoon center on wallpaper when NICT D531108 reports TY "
            "(default: off; use --show-typhoon-marker to enable).",
        )

        self._parser.add_argument(
            "--show-my-location",
            dest="show_my_location",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Mark approximate location from IP geolocation on wallpaper "
            "(default: off; use --show-my-location to enable).",
        )

        self._parser.add_argument(
            "--logging",
            dest="logging_enabled",
            default=None,
            action=argparse.BooleanOptionalAction,
            help="Enable console and file logging (default: off; use --logging to enable).",
        )

        self._parser.add_argument(
            "-v", "--version", action="version", version=f"%(prog)s {SOFTWARE_VERSION}"
        )

        self._args = self._parser.parse_args()

        cli_values = {
            "resolution": self._args.download_resolution,
            "auto_adjust": self._args.is_auto_adjust_picture,
            "margin_top_percent": self._args.margin_top_percent,
            "margin_bottom_percent": self._args.margin_bottom_percent,
            "cleanup_after_apply": self._args.cleanup_after_apply,
            "use_yesterday_local_time": self._args.use_yesterday_local_time,
            "reduce_banding": self._args.reduce_banding,
            "show_typhoon_marker": self._args.show_typhoon_marker,
            "show_my_location": self._args.show_my_location,
            "logging_enabled": self._args.logging_enabled,
        }
        self._resolved = resolve_runtime_settings(cli_values)

    def log_resolved(self) -> None:
        """在日志已初始化后输出合并后的配置。"""
        logging.info("Download resolution (px): %s", self._resolved["resolution"])
        logging.info("Auto margin adjust: %s", self._resolved["auto_adjust"])
        logging.info(
            "Margin percents: top=%s bottom=%s",
            self._resolved["margin_top_percent"],
            self._resolved["margin_bottom_percent"],
        )
        logging.info("Cleanup after apply: %s", self._resolved["cleanup_after_apply"])
        logging.info(
            "Use yesterday local time: %s",
            self._resolved["use_yesterday_local_time"],
        )
        logging.info("Reduce banding: %s", self._resolved["reduce_banding"])
        logging.info("Show typhoon marker: %s", self._resolved["show_typhoon_marker"])
        logging.info("Show my location: %s", self._resolved["show_my_location"])
        logging.info("Logging enabled: %s", self._resolved["logging_enabled"])

    def get_download_resolution(self):
        return self._resolved["resolution"]

    def is_auto_adjust_picture(self):
        return self._resolved["auto_adjust"]

    def get_margin_top_percent(self):
        return self._resolved["margin_top_percent"]

    def get_margin_bottom_percent(self):
        return self._resolved["margin_bottom_percent"]

    def is_cleanup_after_apply(self):
        return self._resolved["cleanup_after_apply"]

    def is_use_yesterday_local_time(self):
        return self._resolved["use_yesterday_local_time"]

    def is_reduce_banding(self):
        return self._resolved["reduce_banding"]

    def is_show_typhoon_marker(self):
        return self._resolved["show_typhoon_marker"]

    def is_show_my_location(self):
        return self._resolved["show_my_location"]

    def is_logging_enabled(self):
        return self._resolved["logging_enabled"]
