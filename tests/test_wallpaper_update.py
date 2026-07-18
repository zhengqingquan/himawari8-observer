"""Seam: pause gates scheduled wallpaper updates; manual can bypass."""

import threading
import unittest

from src.wallpaper_update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)


class WallpaperPauseTests(unittest.TestCase):
    def setUp(self):
        resume()

    def tearDown(self):
        resume()

    def test_pause_and_resume_toggle(self):
        self.assertFalse(is_paused())
        pause()
        self.assertTrue(is_paused())
        resume()
        self.assertFalse(is_paused())

    def test_respect_pause_skips_when_paused(self):
        calls = []
        pause()
        self.assertFalse(
            run_wallpaper_update(
                pipeline=lambda: calls.append(1),
                respect_pause=True,
            )
        )
        self.assertEqual(calls, [])

    def test_manual_runs_while_paused(self):
        calls = []
        pause()
        self.assertTrue(
            run_wallpaper_update(
                pipeline=lambda: calls.append(1),
                respect_pause=False,
            )
        )
        self.assertEqual(calls, [1])


class RunWallpaperUpdateTests(unittest.TestCase):
    def setUp(self):
        resume()

    def tearDown(self):
        resume()

    def test_requires_pipeline(self):
        with self.assertRaises(TypeError):
            run_wallpaper_update()

    def test_runs_pipeline_when_idle(self):
        calls = []

        def pipeline():
            calls.append(1)

        self.assertTrue(run_wallpaper_update(pipeline=pipeline))
        self.assertEqual(calls, [1])

    def test_skips_when_busy(self):
        started = threading.Event()
        release = threading.Event()

        def blocking_pipeline():
            started.set()
            release.wait(timeout=5)

        worker = threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=blocking_pipeline),
            daemon=True,
        )
        worker.start()
        self.assertTrue(started.wait(timeout=2))

        skipped_calls = []
        self.assertFalse(
            run_wallpaper_update(pipeline=lambda: skipped_calls.append(1))
        )
        self.assertEqual(skipped_calls, [])

        release.set()
        worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
