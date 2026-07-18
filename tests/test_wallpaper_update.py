"""Seam: run_wallpaper_update — idle runs pipeline once; busy skips."""

import threading
import unittest

from src.wallpaper_update import run_wallpaper_update


class RunWallpaperUpdateTests(unittest.TestCase):
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
