"""Seam: main wires Config resolution pixel into pipeline grade."""

import unittest

from src.main import main


class MainConfigToPipelineTests(unittest.TestCase):
    def test_main_passes_grade_from_resolution_pixel(self):
        grades = []

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)

        main(
            run_pipeline=fake_pipeline,
            get_resolution_pixel=lambda: 8800,
        )
        self.assertEqual(grades, ["16d"])

    def test_main_maps_default_pixel_to_4d(self):
        grades = []

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)

        main(
            run_pipeline=fake_pipeline,
            get_resolution_pixel=lambda: 2200,
        )
        self.assertEqual(grades, ["4d"])


if __name__ == "__main__":
    unittest.main()
