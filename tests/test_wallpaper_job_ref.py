"""Seam: WallpaperJobRef is shared and can replace frozen grade at runtime."""

import unittest

from src.wallpaper_job import WallpaperJobRef


class WallpaperJobRefTests(unittest.TestCase):
    def test_call_uses_current_grade(self):
        grades = []

        def fake_build(resolution_grade, *, auto_adjust=False):
            def job():
                grades.append((resolution_grade, auto_adjust))

            return job

        ref = WallpaperJobRef("4d", auto_adjust=True, build_job=fake_build)
        ref()
        ref.set_resolution_grade("8d")
        ref()
        self.assertEqual(grades, [("4d", True), ("8d", True)])

    def test_set_pixel_side_maps_to_grade(self):
        grades = []

        def fake_build(resolution_grade, *, auto_adjust=False):
            def job():
                grades.append(resolution_grade)

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build)
        ref.set_pixel_side(8800)
        self.assertEqual(ref.resolution_grade, "16d")
        self.assertEqual(ref.pixel_side, 8800)
        ref()
        self.assertEqual(grades, ["16d"])


if __name__ == "__main__":
    unittest.main()
