"""Scheduler first-run progressive flag."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.scheduler import build_scheduler_tick


class BuildSchedulerTickTests(unittest.TestCase):
    def test_first_tick_progressive_then_not(self):
        calls = []

        def pipeline():
            return None

        with patch("src.scheduler.run_wallpaper_update") as run_update:
            run_update.side_effect = lambda **kwargs: calls.append(dict(kwargs))
            tick = build_scheduler_tick(pipeline)
            tick()
            tick()
            tick()

        self.assertEqual(len(calls), 3)
        self.assertIs(calls[0]["pipeline"], pipeline)
        self.assertTrue(calls[0]["respect_pause"])
        self.assertTrue(calls[0]["progressive"])
        self.assertFalse(calls[1]["progressive"])
        self.assertFalse(calls[2]["progressive"])


if __name__ == "__main__":
    unittest.main()
