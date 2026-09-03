"""Tray observation time formatting (UTC → local)."""

import unittest
from datetime import timedelta, timezone

from src.tray.menu import format_observation_local_time


class FormatObservationLocalTimeTests(unittest.TestCase):
    def test_converts_utc_to_fixed_offset(self):
        china = timezone(timedelta(hours=8))
        self.assertEqual(
            format_observation_local_time("2026-09-03 02:10:00", local_tz=china),
            "2026-09-03 10:10:00",
        )

    def test_negative_offset_crosses_date(self):
        west = timezone(timedelta(hours=-5))
        self.assertEqual(
            format_observation_local_time("2026-09-03 02:10:00", local_tz=west),
            "2026-09-02 21:10:00",
        )


if __name__ == "__main__":
    unittest.main()
