"""Seam: WallpaperJobRef is shared and can replace frozen grade at runtime."""

import unittest

from src.wallpaper_job import WallpaperJobRef


class WallpaperJobRefTests(unittest.TestCase):
    def test_call_uses_current_grade(self):
        grades = []

        def fake_build(resolution_grade, *, auto_adjust=False, **_kwargs):
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

        def fake_build(resolution_grade, *, auto_adjust=False, **_kwargs):
            def job():
                grades.append(resolution_grade)

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build)
        ref.set_pixel_side(8800)
        self.assertEqual(ref.resolution_grade, "16d")
        self.assertEqual(ref.pixel_side, 8800)
        ref()
        self.assertEqual(grades, ["16d"])

    def test_set_margin_rebuilds_job(self):
        builds = []

        def fake_build(
            resolution_grade,
            *,
            auto_adjust=False,
            margin_top_percent=5.0,
            margin_bottom_percent=5.0,
            **_kwargs,
        ):
            builds.append(
                (resolution_grade, auto_adjust, margin_top_percent, margin_bottom_percent)
            )

            def job():
                return None

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build)
        ref.set_margin_bottom_percent(12.0)
        ref.set_auto_adjust(False)
        self.assertEqual(ref.margin_bottom_percent, 12.0)
        self.assertFalse(ref.auto_adjust)
        self.assertEqual(
            builds,
            [
                ("4d", False, 5.0, 5.0),
                ("4d", False, 5.0, 12.0),
                ("4d", False, 5.0, 12.0),
            ],
        )

    def test_set_cleanup_after_apply_rebuilds_job(self):
        flags = []

        def fake_build(resolution_grade, *, cleanup_after_apply=True, **_kwargs):
            flags.append(cleanup_after_apply)

            def job():
                return None

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build)
        self.assertTrue(ref.cleanup_after_apply)
        ref.set_cleanup_after_apply(False)
        self.assertFalse(ref.cleanup_after_apply)
        self.assertEqual(flags, [True, False])


if __name__ == "__main__":
    unittest.main()
