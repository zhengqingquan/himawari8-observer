"""开机启动：读写当前用户 Run 注册表项。"""

from __future__ import annotations

import logging
import os
import sys
import winreg as reg

from src.metadata.soft_info import PROGRAM_NAME

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
            logging.info(f"Startup entry found: {value}")
            return True
    except FileNotFoundError:
        logging.info("The startup entry does not exist.")
    except Exception as e:
        logging.error(f"Error checking startup entry: {e}")
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
        logging.info(f"Successfully added {exe_path} to startup.")
    except Exception as e:
        logging.error(f"Failed to add to startup: {e}")


def remove_from_startup_exe() -> None:
    """删除开机启动项（若不存在则忽略）。"""
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(reg_key, app_name)
        reg.CloseKey(reg_key)
        logging.info("Successfully removed from startup.")
    except FileNotFoundError:
        logging.info("The specified key does not exist.")
    except Exception as e:
        logging.error(f"Failed to remove from startup: {e}")
