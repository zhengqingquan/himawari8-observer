"""Seam: build_wallpaper_job freezes resolution grade and auto_adjust at assembly."""

import unittest
from types import SimpleNamespace

from src.wallpaper.job import build_wallpaper_job, job_kwargs_from_config


class JobKwargsFromConfigTests(unittest.TestCase):
    def test_maps_config_getters(self):
        config = SimpleNamespace(
            get_download_resolution=lambda: 2200,
            is_auto_adjust_picture=lambda: True,
            get_margin_top_percent=lambda: 1.0,
            get_margin_bottom_percent=lambda: 2.0,
            is_cleanup_after_apply=lambda: False,
            is_use_yesterday_local_time=lambda: True,
            is_reduce_banding=lambda: True,
            is_show_typhoon_marker=lambda: True,
        )
        kwargs = job_kwargs_from_config(config)
        self.assertEqual(kwargs["resolution_grade"], "4d")
        self.assertTrue(kwargs["auto_adjust"])
        self.assertEqual(kwargs["margin_top_percent"], 1.0)
        self.assertEqual(kwargs["margin_bottom_percent"], 2.0)
        self.assertFalse(kwargs["cleanup_after_apply"])
        self.assertTrue(kwargs["use_yesterday_local_time"])
        self.assertTrue(kwargs["reduce_banding"])
        self.assertTrue(kwargs["show_typhoon_marker"])


class BuildWallpaperJobTests(unittest.TestCase):
    def test_job_uses_grade_from_assembly(self):
        grades = []

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)

        job = build_wallpaper_job("16d", run_pipeline=fake_pipeline)
        job()
        job()
        self.assertEqual(grades, ["16d", "16d"])

    def test_job_does_not_reread_external_pixel(self):
        grades = []
        pixels = [8800]

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)

        # Grade is fixed at build time; changing pixels later must not matter.
        job = build_wallpaper_job("8d", run_pipeline=fake_pipeline)
        pixels[0] = 550
        job()
        self.assertEqual(grades, ["8d"])

    def test_job_freezes_auto_adjust(self):
        flags = []

        def fake_pipeline(*, auto_adjust=False, **_kwargs):
            flags.append(auto_adjust)

        job = build_wallpaper_job("4d", auto_adjust=True, run_pipeline=fake_pipeline)
        job()
        job()
        self.assertEqual(flags, [True, True])

    def test_job_freezes_margin_percents(self):
        margins = []

        def fake_pipeline(*, margin_top_percent=5.0, margin_bottom_percent=5.0, **_kwargs):
            margins.append((margin_top_percent, margin_bottom_percent))

        job = build_wallpaper_job(
            "4d",
            margin_top_percent=3.0,
            margin_bottom_percent=12.0,
            run_pipeline=fake_pipeline,
        )
        job()
        self.assertEqual(margins, [(3.0, 12.0)])

    def test_job_skips_second_identical_run_via_state(self):
        calls = []

        def fake_pipeline(*, applied_run_state=None, **_kwargs):
            calls.append(applied_run_state)
            if applied_run_state is not None and applied_run_state.get("last") == "done":
                return
            if applied_run_state is not None:
                applied_run_state["last"] = "done"

        job = build_wallpaper_job("4d", run_pipeline=fake_pipeline)
        job()
        job()
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0], calls[1])
        self.assertEqual(calls[0]["last"], "done")


if __name__ == "__main__":
    unittest.main()
