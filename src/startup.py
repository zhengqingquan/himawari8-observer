"""
让程序开机自启动。
这需要用到win32api和win32gui
"""

# import win32api, win32gui

# 获取控制台标题
# ct = win32api.GetConsoleTitle()
# 查找窗口句柄
# hd = win32gui.FindWindow(0,ct)
# 隐藏窗口控制台。
# win32gui.ShowWindow(hd,0)


# 需要启动脚本

# cd C:\project\SoilMoisture（定位到python文件目录）
#
# start test.py（启动程序）

# ----------------------------------------------------

import os
import sys
import winreg as reg

def add_to_startup(script_path):
    # 获取当前Python解释器的路径
    python_exe = sys.executable
    
    # 获取当前脚本的绝对路径
    script_abs_path = os.path.abspath(script_path)
    
    # 注册表的路径
    key = r'Software\Microsoft\Windows\CurrentVersion\Run'
    
    # 打开注册表键，准备写入
    with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_ALL_ACCESS) as reg_key:
        # 将脚本添加到启动项
        reg.SetValueEx(reg_key, 'TimeLogger', 0, reg.REG_SZ, f'"{python_exe}" "{script_abs_path}"')

def remove_from_startup():
    # 注册表的路径
    key = r'Software\Microsoft\Windows\CurrentVersion\Run'
    
    # 打开注册表键，准备写入
    with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_ALL_ACCESS) as reg_key:
        # 删除启动项
        reg.DeleteValue(reg_key, 'TimeLogger')

# if __name__ == "__main__":
#     # 检查命令行参数
#     if len(sys.argv) > 1 and sys.argv[1] == 'remove':
#         remove_from_startup()
#     else:
#         # 将当前脚本路径传入函数
#         add_to_startup(__file__)

if __name__ == "__main__":

# 计算机\HKEY_USERS\S-1-5-21-4062772115-2734147629-900880185-1001\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
# TimeLogger
# "C:\Python312\python.exe" "g:\work\himawari8-observer\scr\startup.py"
# "C:\Python312\python.exe" "G:\work\himawari8-observer\scr\main.py"

    # 将当前脚本路径传入函数
    # add_to_startup(__file__)
    # add_to_startup(r'scr/main.py')

    remove_from_startup()

    print('i lov my city')
    input('Press Enter to exit...')
