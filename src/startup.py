import os
import sys
import winreg as reg
import logging
from src.metadata.soft_info import PROGRAM_NAME

key_value = r'Software\Microsoft\Windows\CurrentVersion\Run'
app_name = PROGRAM_NAME

def is_startup_set():
    # key = reg.HKEY_CURRENT_USER
    # key_value = r'Software\Microsoft\Windows\CurrentVersion\Run'
    # app_name = 'MyPythonApp'
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_READ)
        value, reg_type = reg.QueryValueEx(reg_key, app_name)
        reg.CloseKey(reg_key)
        if value:
            logging.info(f'Startup entry found: {value}')
            return True
    except FileNotFoundError:
        logging.info('The startup entry does not exist.')
    except Exception as e:
        logging.error(f'Error checking startup entry: {e}')
    return False

def add_to_startup_exe(exe_path=None):
    if exe_path is None:
        exe_path = os.path.abspath(sys.argv[0])
    # key = reg.HKEY_CURRENT_USER
    # key_value = r'Software\Microsoft\Windows\CurrentVersion\Run'

    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, exe_path)
        reg.CloseKey(reg_key)
        logging.info(f'Successfully added {exe_path} to startup.')
    except Exception as e:
        logging.ERROR(f'Failed to add to startup: {e}')

def remove_from_startup_exe():
    # key = reg.HKEY_CURRENT_USER
    # key_value = r'Software\Microsoft\Windows\CurrentVersion\Run'

    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_value, 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(reg_key, app_name)
        reg.CloseKey(reg_key)
        logging.info('Successfully removed from startup.')
    except FileNotFoundError:
        logging.info('The specified key does not exist.')
    except Exception as e:
        logging.error(f'Failed to remove from startup: {e}')
