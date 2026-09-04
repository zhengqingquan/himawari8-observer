"""Logging enable/disable seam."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.log import init_logging, is_logging_enabled, set_logging_enabled


class LoggingToggleTests(unittest.TestCase):
    def tearDown(self):
        set_logging_enabled(False)

    def test_default_init_disables_logging(self):
        init_logging()
        self.assertFalse(is_logging_enabled())

    def test_enable_and_disable(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "debug_log.txt"
            with patch("src.log.LOG_PATH", log_path):
                set_logging_enabled(True)
                self.assertTrue(is_logging_enabled())
                logging.info("hello-log-toggle")
                set_logging_enabled(False)
                self.assertFalse(is_logging_enabled())
                self.assertTrue(log_path.is_file())
                self.assertIn("hello-log-toggle", log_path.read_text(encoding="utf-8"))

    def test_enabling_quiets_third_party_loggers(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "debug_log.txt"
            with patch("src.log.LOG_PATH", log_path):
                set_logging_enabled(True)
                try:
                    self.assertEqual(logging.getLogger("urllib3").level, logging.WARNING)
                    self.assertEqual(logging.getLogger("PIL").level, logging.WARNING)
                    self.assertEqual(
                        logging.getLogger("PIL.PngImagePlugin").level,
                        logging.WARNING,
                    )
                finally:
                    set_logging_enabled(False)


if __name__ == "__main__":
    unittest.main()
