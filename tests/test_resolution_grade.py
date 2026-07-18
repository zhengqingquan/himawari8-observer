"""Seam: resolution grade — pixel ↔ Nd mapping and live default."""

import unittest

from src.resolution_grade import (
    default_grade,
    grade_to_grid,
    pixel_to_grade,
    supported_pixels,
    tile_pixel,
)


class ResolutionGradeTests(unittest.TestCase):
    def test_tile_pixel_is_550(self):
        self.assertEqual(tile_pixel(), 550)

    def test_default_grade_is_4d(self):
        self.assertEqual(default_grade(), "4d")

    def test_grade_to_grid(self):
        self.assertEqual(grade_to_grid("1d"), 1)
        self.assertEqual(grade_to_grid("4d"), 4)
        self.assertEqual(grade_to_grid("8d"), 8)
        self.assertEqual(grade_to_grid("16d"), 16)
        self.assertEqual(grade_to_grid("20d"), 20)

    def test_pixel_to_grade(self):
        self.assertEqual(pixel_to_grade(550), "1d")
        self.assertEqual(pixel_to_grade(2200), "4d")
        self.assertEqual(pixel_to_grade(4400), "8d")
        self.assertEqual(pixel_to_grade(8800), "16d")
        self.assertEqual(pixel_to_grade(11000), "20d")

    def test_supported_pixels_match_grades(self):
        pixels = supported_pixels()
        self.assertEqual(pixels, [550, 2200, 4400, 8800, 11000])
        for px in pixels:
            grade = pixel_to_grade(px)
            self.assertEqual(tile_pixel() * grade_to_grid(grade), px)

    def test_unknown_grade_raises(self):
        with self.assertRaises(ValueError):
            grade_to_grid("3d")

    def test_unknown_pixel_raises(self):
        with self.assertRaises(ValueError):
            pixel_to_grade(1000)


if __name__ == "__main__":
    unittest.main()
