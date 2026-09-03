"""Logging enable/disable seam."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.log.log import init_logging, is_logging_enabled, set_logging_enabled


class LoggingToggleTests(unittest.TestCase):
    def tearDown(self):
        set_logging_enabled(False)

    def test_default_init_disables_logging(self):
        init_logging()
        self.assertFalse(is_logging_enabled())

    def test_enable_and_disable(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "debug_log.txt"
            with patch("src.log.log.LOG_PATH", log_path):
                set_logging_enabled(True)
                self.assertTrue(is_logging_enabled())
                logging.info("hello-log-toggle")
                set_logging_enabled(False)
                self.assertFalse(is_logging_enabled())
                self.assertTrue(log_path.is_file())
                self.assertIn("hello-log-toggle", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
