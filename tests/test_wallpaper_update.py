"""Seam: pause gates scheduled wallpaper updates; manual can bypass; busy queues follow-up."""

import threading
import unittest

import src.wallpaper.update as update_mod
from src.wallpaper.update import (
    is_paused,
    pause,
    resume,
    run_wallpaper_update,
)


def _reset_update_gates() -> None:
    resume()
    with update_mod._pending_lock:
        update_mod._pending_run = False
        update_mod._pending_progressive = False
        update_mod._pending_bypass_pause = False


class WallpaperPauseTests(unittest.TestCase):
    def setUp(self):
        _reset_update_gates()

    def tearDown(self):
        _reset_update_gates()

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
        _reset_update_gates()

    def tearDown(self):
        _reset_update_gates()

    def test_requires_pipeline(self):
        with self.assertRaises(TypeError):
            run_wallpaper_update()

    def test_runs_pipeline_when_idle(self):
        calls = []

        def pipeline():
            calls.append(1)

        self.assertTrue(run_wallpaper_update(pipeline=pipeline))
        self.assertEqual(calls, [1])

    def test_queues_follow_up_when_busy(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def blocking_pipeline():
            calls.append(1)
            started.set()
            release.wait(timeout=5)

        worker = threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=blocking_pipeline),
            daemon=True,
        )
        worker.start()
        self.assertTrue(started.wait(timeout=2))

        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline))
        self.assertEqual(len(calls), 1)

        release.set()
        worker.join(timeout=2)
        self.assertEqual(len(calls), 2)

    def test_coalesces_multiple_busy_triggers_into_one_follow_up(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def blocking_pipeline():
            calls.append(1)
            if len(calls) == 1:
                started.set()
                release.wait(timeout=5)

        worker = threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=blocking_pipeline),
            daemon=True,
        )
        worker.start()
        self.assertTrue(started.wait(timeout=2))

        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline))
        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline))
        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline))
        self.assertEqual(len(calls), 1)

        release.set()
        worker.join(timeout=2)
        self.assertEqual(len(calls), 2)

    def test_queued_respect_pause_dropped_when_paused(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def blocking_pipeline():
            calls.append(1)
            started.set()
            release.wait(timeout=5)

        worker = threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=blocking_pipeline),
            daemon=True,
        )
        worker.start()
        self.assertTrue(started.wait(timeout=2))

        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline, respect_pause=True))
        pause()
        release.set()
        worker.join(timeout=2)
        self.assertEqual(len(calls), 1)

    def test_queued_manual_runs_even_when_paused(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def blocking_pipeline():
            calls.append(1)
            started.set()
            release.wait(timeout=5)

        worker = threading.Thread(
            target=lambda: run_wallpaper_update(pipeline=blocking_pipeline),
            daemon=True,
        )
        worker.start()
        self.assertTrue(started.wait(timeout=2))

        self.assertFalse(run_wallpaper_update(pipeline=blocking_pipeline, respect_pause=False))
        pause()
        release.set()
        worker.join(timeout=2)
        self.assertEqual(len(calls), 2)

    def test_progressive_uses_run_progressive_when_available(self):
        calls = []

        class ProgressivePipeline:
            def __call__(self):
                calls.append("call")

            def run_progressive(self):
                calls.append("progressive")

        self.assertTrue(run_wallpaper_update(pipeline=ProgressivePipeline(), progressive=True))
        self.assertEqual(calls, ["progressive"])

    def test_progressive_falls_back_to_call(self):
        calls = []
        self.assertTrue(
            run_wallpaper_update(
                pipeline=lambda: calls.append("call"),
                progressive=True,
            )
        )
        self.assertEqual(calls, ["call"])


if __name__ == "__main__":
    unittest.main()
