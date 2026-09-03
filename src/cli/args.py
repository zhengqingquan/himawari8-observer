"""CLI 参数解析：单例 Config。"""

from __future__ import annotations

import argparse
import logging

from src.metadata.soft_config import (
    DEFAULT_MARGIN_BOTTOM_PERCENT,
    DEFAULT_MARGIN_TOP_PERCENT,
    DEFAULT_RESOLUTION,
    IMAGE_RESOLUTION,
)
from src.metadata.soft_info import DESCRIPTION, EPILOG, PROGRAM_NAME, SOFTWARE_VERSION


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
    """进程内单例：解析并缓存命令行参数。"""

    _instance = None
    _parser = None
    _args = None

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
        """定义并解析 CLI 参数。"""
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
            default=DEFAULT_RESOLUTION,
            const=DEFAULT_RESOLUTION,
            action="store",
            dest="download_resolution",
            nargs="?",
            help='"equal" represents how many 550-pixel images one side of an image is equal to.',
        )

        self._parser.add_argument(
            "-a",
            "--adjust",
            dest="is_auto_adjust_picture",
            default=True,
            action=argparse.BooleanOptionalAction,
            help="Pad wallpaper with black borders so the taskbar covers the margin "
            "(default: on; use --no-adjust to disable).",
        )

        self._parser.add_argument(
            "--margin-top",
            type=_percent,
            default=DEFAULT_MARGIN_TOP_PERCENT,
            dest="margin_top_percent",
            help="Top black-border percent of the square image side (default: 5).",
        )

        self._parser.add_argument(
            "--margin-bottom",
            type=_percent,
            default=DEFAULT_MARGIN_BOTTOM_PERCENT,
            dest="margin_bottom_percent",
            help="Bottom black-border percent of the square image side (default: 5).",
        )

        self._parser.add_argument(
            "--cleanup-after-apply",
            dest="cleanup_after_apply",
            default=True,
            action=argparse.BooleanOptionalAction,
            help="After setting wallpaper, delete tiles and old img folders "
            "but keep the current wallpaper file (default: on; "
            "use --no-cleanup-after-apply to disable).",
        )

        self._parser.add_argument(
            "-v", "--version", action="version", version=f"%(prog)s {SOFTWARE_VERSION}"
        )

        self._args = self._parser.parse_args()

        logging.info(f"Download resolution: {self._args.download_resolution}")
        logging.info(f"Is auto adjust picture: {self._args.is_auto_adjust_picture}")
        logging.info(
            "Margin percents: top=%s bottom=%s",
            self._args.margin_top_percent,
            self._args.margin_bottom_percent,
        )
        logging.info(f"Cleanup after apply: {self._args.cleanup_after_apply}")

    # TODO 可以重新解析参数。
    def parse_known_args(self, args):
        self._parser.parse_known_args(args)

    def get_download_resolution(self):
        return self._args.download_resolution

    def is_auto_adjust_picture(self):
        return self._args.is_auto_adjust_picture

    def get_margin_top_percent(self):
        return self._args.margin_top_percent

    def get_margin_bottom_percent(self):
        return self._args.margin_bottom_percent

    def is_cleanup_after_apply(self):
        return self._args.cleanup_after_apply
