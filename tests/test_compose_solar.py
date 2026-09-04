"""subsolar / sunglint latlon anchors."""

from __future__ import annotations

import unittest
from time import strptime

from src.compose.solar import subsolar_latlon, sunglint_latlon


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


class SunglintLatlonTests(unittest.TestCase):
    def test_between_subsolar_and_sub_satellite(self):
        obs = strptime("2026-09-04 04:20:00", "%Y-%m-%d %H:%M:%S")
        sun_lat, sun_lon = subsolar_latlon(obs)
        glint_lat, glint_lon = sunglint_latlon(obs)
        # 耀斑应落在直射点与星下点 (0, 140.7°E) 之间
        self.assertGreater(glint_lat, 0.0)
        self.assertLess(glint_lat, sun_lat)
        lo, hi = sorted((sun_lon, 140.7))
        self.assertGreaterEqual(glint_lon, lo - 0.5)
        self.assertLessEqual(glint_lon, hi + 0.5)
        self.assertNotAlmostEqual(glint_lon, sun_lon, delta=1.0)


if __name__ == "__main__":
    unittest.main()
