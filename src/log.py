"""日志初始化：可开关；默认关闭。"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src.metadata.app_config import LOG_PATH

_CONSOLE_HANDLER_NAME = "himawari8_console"
_FILE_HANDLER_NAME = "himawari8_file"
_LOG_MAX_BYTES = 2 * 1024 * 1024
_LOG_BACKUP_COUNT = 3
_NOISY_LOGGER_NAMES = (
    "urllib3",
    "urllib3.connectionpool",
    "PIL",
    "PIL.Image",
    "PIL.PngImagePlugin",
)
_enabled = False


def is_logging_enabled() -> bool:
    """当前是否已启用日志输出。"""
    return _enabled


def _has_handler(logger: logging.Logger, name: str) -> bool:
    return any(getattr(handler, "name", None) == name for handler in logger.handlers)


def _quiet_third_party_loggers() -> None:
    """压低 urllib3 / Pillow 等库的 DEBUG，避免刷屏。"""
    for name in _NOISY_LOGGER_NAMES:
        logging.getLogger(name).setLevel(logging.WARNING)


def _attach_handlers() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.disabled = False
    _quiet_third_party_loggers()

    if not _has_handler(logger, _CONSOLE_HANDLER_NAME):
        console_handler = logging.StreamHandler()
        console_handler.name = _CONSOLE_HANDLER_NAME
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(console_handler)

    if not _has_handler(logger, _FILE_HANDLER_NAME):
        file_handler = RotatingFileHandler(
            LOG_PATH,
            maxBytes=_LOG_MAX_BYTES,
            backupCount=_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.name = _FILE_HANDLER_NAME
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
            )
        )
        logger.addHandler(file_handler)


def _detach_handlers() -> None:
    logger = logging.getLogger()
    for handler in list(logger.handlers):
        if getattr(handler, "name", None) in {_CONSOLE_HANDLER_NAME, _FILE_HANDLER_NAME}:
            logger.removeHandler(handler)
            handler.close()


def set_logging_enabled(enabled: bool) -> None:
    """启用或关闭控制台与文件日志。"""
    global _enabled
    if enabled:
        _attach_handlers()
        _enabled = True
        logging.info("Logging enabled; file: %s", LOG_PATH)
    else:
        _enabled = False
        _detach_handlers()


def init_logging(*, enabled: bool = False) -> None:
    """按开关配置根 logger；默认关闭。"""
    set_logging_enabled(enabled)
