"""日志初始化：控制台 INFO + 文件 DEBUG。"""

from __future__ import annotations

import logging

from src.metadata.soft_config import LOG_PATH


def init_logging() -> None:
    """配置根 logger：控制台与 ``LOG_PATH`` 文件双输出。"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    logging.info(f"Log path：{LOG_PATH}")
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
        )
    )
    logger.addHandler(file_handler)
