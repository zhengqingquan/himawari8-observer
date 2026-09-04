"""himawari8.fd lat/lon → pixel projection."""

from __future__ import annotations

import unittest

from src.compose.geo import latlon_to_himawari_fd_xy


class HimawariFdProjectionTests(unittest.TestCase):
    def test_har_typhoon_center_on_2d_side_is_on_disk(self):
        # HAR D531108 sample center; 2d → side 1100
        xy = latlon_to_himawari_fd_xy(29.024, 128.437, 1100)
        self.assertIsNotNone(xy)
        x, y = xy
        self.assertGreaterEqual(x, 0)
        self.assertLess(x, 1100)
        self.assertGreaterEqual(y, 0)
        self.assertLess(y, 1100)
        # West of sub-satellite (~140.7°E) → left half; mid-lat Northern → upper half
        self.assertLess(x, 550)
        self.assertLess(y, 550)

    def test_invalid_side_returns_none(self):
        self.assertIsNone(latlon_to_himawari_fd_xy(0.0, 140.7, 0))


if __name__ == "__main__":
    unittest.main()
