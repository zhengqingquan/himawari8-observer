"""Scheduler first-run progressive flag and reschedule."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.scheduler import build_scheduler_tick, reschedule_interval
from src.wallpaper.job import WallpaperJobRef
from src.wallpaper.update import pause, resume


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


class RescheduleIntervalTests(unittest.TestCase):
    def test_reschedule_calls_scheduler_when_started(self):
        mock_scheduler = MagicMock()
        with patch("src.scheduler._scheduler", mock_scheduler):
            reschedule_interval(900)
        mock_scheduler.reschedule_job.assert_called_once_with(
            "wallpaper_tick",
            trigger="interval",
            seconds=900,
        )

    def test_reschedule_noop_when_not_started(self):
        with patch("src.scheduler._scheduler", None):
            reschedule_interval(600)  # must not raise


class DownloadIntervalJobTests(unittest.TestCase):
    def tearDown(self):
        resume()

    def test_set_interval_reschedules_and_resumes(self):
        pause()
        ref = WallpaperJobRef("4d", persist_state=False)
        with patch("src.wallpaper.job.reschedule_interval") as mock_reschedule:
            with patch("src.wallpaper.job.is_paused", return_value=True):
                with patch("src.wallpaper.job.resume") as mock_resume:
                    ref.set_download_interval_minutes(15)
        self.assertEqual(ref.download_interval_minutes, 15)
        mock_reschedule.assert_called_once_with(15 * 60)
        mock_resume.assert_called_once()

    def test_set_invalid_interval_ignored(self):
        ref = WallpaperJobRef("4d", persist_state=False)
        with patch("src.wallpaper.job.reschedule_interval") as mock_reschedule:
            ref.set_download_interval_minutes(7)
        self.assertEqual(ref.download_interval_minutes, 10)
        mock_reschedule.assert_not_called()


if __name__ == "__main__":
    unittest.main()
