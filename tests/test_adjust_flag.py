"""Seam: -a / --adjust defaults on; margin percents default to 5."""

import sys
import unittest
from unittest.mock import patch

from src.cli.args import Config


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

    def test_default_cleanup_after_apply_is_true(self):
        config = _fresh_config(["run.py"])
        self.assertTrue(config.is_cleanup_after_apply())

    def test_no_cleanup_after_apply_disables(self):
        config = _fresh_config(["run.py", "--no-cleanup-after-apply"])
        self.assertFalse(config.is_cleanup_after_apply())

    def test_default_margin_percents_are_five(self):
        config = _fresh_config(["run.py"])
        self.assertEqual(config.get_margin_top_percent(), 5.0)
        self.assertEqual(config.get_margin_bottom_percent(), 5.0)

    def test_margin_percents_can_be_set(self):
        config = _fresh_config(
            ["run.py", "--margin-top", "3", "--margin-bottom", "12.5"]
        )
        self.assertEqual(config.get_margin_top_percent(), 3.0)
        self.assertEqual(config.get_margin_bottom_percent(), 12.5)


if __name__ == "__main__":
    unittest.main()
