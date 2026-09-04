"""Tray observation time formatting (UTC → local) and icon title."""

import unittest
from datetime import timedelta, timezone

from src.metadata.app_info import PROGRAM_NAME
from src.tray.actions import format_observation_local_time, format_tray_icon_title


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

    def test_includes_local_utc_and_resolution(self):
        china = timezone(timedelta(hours=8))
        self.assertEqual(
            format_tray_icon_title(
                "2026-09-03 02:10:00",
                pixel_side=11000,
                local_tz=china,
            ),
            "\n".join(
                [
                    PROGRAM_NAME,
                    "壁纸时间（本地）：2026-09-03 10:10:00",
                    "壁纸时间（UTC）：2026-09-03 02:10:00",
                    "分辨率：11000",
                ]
            ),
        )

    def test_omits_resolution_when_missing(self):
        china = timezone(timedelta(hours=8))
        self.assertEqual(
            format_tray_icon_title("2026-09-03 02:10:00", local_tz=china),
            "\n".join(
                [
                    PROGRAM_NAME,
                    "壁纸时间（本地）：2026-09-03 10:10:00",
                    "壁纸时间（UTC）：2026-09-03 02:10:00",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
