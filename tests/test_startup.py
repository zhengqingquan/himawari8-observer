"""开机启动注册表同步。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.startup import apply_startup_enabled


class ApplyStartupEnabledTests(unittest.TestCase):
    def test_enabled_adds_startup_entry(self):
        with (
            patch("src.startup.add_to_startup_exe") as add,
            patch("src.startup.remove_from_startup_exe") as remove,
        ):
            apply_startup_enabled(True, exe_path=r"E:\app\himawari8-observer.exe")
            add.assert_called_once_with(exe_path=r"E:\app\himawari8-observer.exe")
            remove.assert_not_called()

    def test_disabled_removes_startup_entry(self):
        with (
            patch("src.startup.add_to_startup_exe") as add,
            patch("src.startup.remove_from_startup_exe") as remove,
        ):
            apply_startup_enabled(False)
            remove.assert_called_once_with()
            add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
