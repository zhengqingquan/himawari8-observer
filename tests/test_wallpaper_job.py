"""Seam: build_wallpaper_job freezes resolution grade and auto_adjust at assembly."""

import unittest

from src.wallpaper_job import build_wallpaper_job


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


if __name__ == "__main__":
    unittest.main()
