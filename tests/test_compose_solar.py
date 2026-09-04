"""subsolar_latlon: equinox / solstice anchors and noon longitude."""

from __future__ import annotations

import unittest
from time import strptime

from src.compose.solar import subsolar_latlon


class SubsolarLatlonTests(unittest.TestCase):
    def test_march_equinox_latitude_near_zero(self):
        # 2026-03-20 16:46 UTC ≈ March equinox
        lat, _lon = subsolar_latlon(strptime("2026-03-20 16:46:00", "%Y-%m-%d %H:%M:%S"))
        self.assertAlmostEqual(lat, 0.0, delta=0.5)

    def test_june_solstice_latitude_near_tropic(self):
        # 2026-06-21 08:24 UTC ≈ June solstice
        lat, _lon = subsolar_latlon(strptime("2026-06-21 08:24:00", "%Y-%m-%d %H:%M:%S"))
        self.assertAlmostEqual(lat, 23.44, delta=0.5)

    def test_utc_noon_longitude_near_greenwich(self):
        lat, lon = subsolar_latlon(strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S"))
        self.assertAlmostEqual(lat, 0.0, delta=1.0)
        # 均时差会偏移数度；正午应在格林尼治附近
        self.assertAlmostEqual(lon, 0.0, delta=5.0)

    def test_longitude_normalized(self):
        _lat, lon = subsolar_latlon(strptime("2026-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
        self.assertGreaterEqual(lon, -180.0)
        self.assertLessEqual(lon, 180.0)


if __name__ == "__main__":
    unittest.main()
