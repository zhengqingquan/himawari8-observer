"""开机启动：读写当前用户 Run 注册表项。"""

from __future__ import annotations

import logging
import os
import sys
import winreg as reg

from src.metadata.app_info import PROGRAM_NAME

key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
app_name = PROGRAM_NAME


def is_startup_set() -> bool:
    """检查是否已写入开机启动项。

    Returns:
        已存在且有值时为 True。
    """
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_READ)
        value, reg_type = reg.QueryValueEx(reg_key, app_name)
        reg.CloseKey(reg_key)
        if value:
            logging.info("Startup entry found: %s", value)
            return True
        logging.info("Startup entry exists but is empty")
    except FileNotFoundError:
        logging.info("Startup entry not set")
    except OSError:
        logging.exception("Failed to check startup entry")
    return False


def add_to_startup_exe(exe_path=None) -> None:
    """将可执行路径写入开机启动。

    Args:
        exe_path: 启动命令路径；默认 ``sys.argv[0]`` 的绝对路径。
    """
    if exe_path is None:
        exe_path = os.path.abspath(sys.argv[0])

    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, exe_path)
        reg.CloseKey(reg_key)
        logging.info("Added startup entry: %s", exe_path)
    except OSError:
        logging.exception("Failed to add startup entry: %s", exe_path)


def remove_from_startup_exe() -> None:
    """删除开机启动项（若不存在则忽略）。"""
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(reg_key, app_name)
        reg.CloseKey(reg_key)
        logging.info("Removed startup entry")
    except FileNotFoundError:
        logging.info("Startup entry already absent")
    except OSError:
        logging.exception("Failed to remove startup entry")


def apply_startup_enabled(enabled: bool, *, exe_path=None) -> None:
    """按开关同步注册表开机启动项（默认关闭时确保项不存在）。"""
    if enabled:
        add_to_startup_exe(exe_path=exe_path)
    else:
        remove_from_startup_exe()
