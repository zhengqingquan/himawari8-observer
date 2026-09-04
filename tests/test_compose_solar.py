"""subsolar / sunglint latlon anchors."""

from __future__ import annotations

import math
import unittest
from time import strptime

from src.compose.solar import is_sunlit, points_on_solar_mu_circle, subsolar_latlon, sunglint_latlon


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


class IsSunlitTests(unittest.TestCase):
    def test_near_subsolar_is_day(self):
        obs = strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S")
        sun_lat, sun_lon = subsolar_latlon(obs)
        self.assertTrue(is_sunlit(sun_lat, sun_lon, obs))

    def test_antipode_is_night(self):
        obs = strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S")
        sun_lat, sun_lon = subsolar_latlon(obs)
        antipode_lat = -sun_lat
        antipode_lon = sun_lon + 180.0 if sun_lon <= 0.0 else sun_lon - 180.0
        self.assertFalse(is_sunlit(antipode_lat, antipode_lon, obs))

    def test_equinox_noon_longitude_boundary(self):
        # 春分正午直射点近格林尼治：±90° 经度附近为晨昏线
        obs = strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S")
        _sun_lat, sun_lon = subsolar_latlon(obs)
        self.assertTrue(is_sunlit(0.0, sun_lon + 45.0, obs))
        self.assertTrue(is_sunlit(0.0, sun_lon - 45.0, obs))
        self.assertFalse(is_sunlit(0.0, sun_lon + 135.0, obs))
        self.assertFalse(is_sunlit(0.0, sun_lon - 135.0, obs))


class PointsOnSolarMuCircleTests(unittest.TestCase):
    def test_mu_zero_points_have_near_zero_dot(self):
        obs = strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S")
        points = points_on_solar_mu_circle(obs, 0.0, sample_count=36)
        self.assertEqual(len(points), 36)
        sun_lat, sun_lon = subsolar_latlon(obs)
        sx = math.cos(math.radians(sun_lat)) * math.cos(math.radians(sun_lon))
        sy = math.cos(math.radians(sun_lat)) * math.sin(math.radians(sun_lon))
        sz = math.sin(math.radians(sun_lat))
        for lat, lon in points:
            lat_r = math.radians(lat)
            lon_r = math.radians(lon)
            px = math.cos(lat_r) * math.cos(lon_r)
            py = math.cos(lat_r) * math.sin(lon_r)
            pz = math.sin(lat_r)
            self.assertAlmostEqual(sx * px + sy * py + sz * pz, 0.0, delta=1e-6)

    def test_abs_mu_over_one_empty(self):
        obs = strptime("2026-03-20 12:00:00", "%Y-%m-%d %H:%M:%S")
        self.assertEqual(points_on_solar_mu_circle(obs, 1.5), [])


if __name__ == "__main__":
    unittest.main()
