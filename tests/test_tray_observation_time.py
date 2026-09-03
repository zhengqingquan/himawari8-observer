"""Tray observation time formatting (UTC → local) and icon title."""

import unittest
from datetime import timedelta, timezone

from src.metadata.soft_info import PROGRAM_NAME
from src.tray.menu import format_observation_local_time, format_tray_icon_title


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


class FormatTrayIconTitleTests(unittest.TestCase):
    def test_none_returns_program_name(self):
        self.assertEqual(format_tray_icon_title(None), PROGRAM_NAME)

    def test_includes_local_time(self):
        china = timezone(timedelta(hours=8))
        self.assertEqual(
            format_tray_icon_title("2026-09-03 02:10:00", local_tz=china),
            f"{PROGRAM_NAME}\n壁纸时间（本地）：2026-09-03 10:10:00",
        )


if __name__ == "__main__":
    unittest.main()
