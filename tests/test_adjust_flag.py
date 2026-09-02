"""Seam: -a / --adjust defaults on; --no-adjust disables."""

import sys
import unittest
from unittest.mock import patch

from src.arg.arg import Config


def _fresh_config(argv):
    Config._instance = None
    with patch.object(sys, "argv", argv):
        return Config()


class AdjustFlagTests(unittest.TestCase):
    def tearDown(self):
        Config._instance = None

    def test_default_adjust_is_true(self):
        config = _fresh_config(["run.py"])
        self.assertTrue(config.is_auto_adjust_picture())

    def test_short_flag_enables_adjust(self):
        config = _fresh_config(["run.py", "-a"])
        self.assertTrue(config.is_auto_adjust_picture())

    def test_long_flag_enables_adjust(self):
        config = _fresh_config(["run.py", "--adjust"])
        self.assertTrue(config.is_auto_adjust_picture())

    def test_no_adjust_disables(self):
        config = _fresh_config(["run.py", "--no-adjust"])
        self.assertFalse(config.is_auto_adjust_picture())


if __name__ == "__main__":
    unittest.main()
