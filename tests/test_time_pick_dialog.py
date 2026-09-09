"""Seam: time-pick dialog parses local date/time and rejects future."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.tray.time_pick_dialog import _default_local_fields, _parse_local_inputs


class TimePickDialogParseTests(unittest.TestCase):
    def test_parse_valid_local_inputs(self):
        past = datetime.now().astimezone() - timedelta(hours=2)
        date_text = past.strftime("%Y-%m-%d")
        time_text = past.strftime("%H:%M")
        got = _parse_local_inputs(date_text, time_text)
        self.assertIsInstance(got, datetime)

    def test_reject_bad_date(self):
        self.assertEqual(_parse_local_inputs("2026/09/01", "10:00"), "日期格式应为 YYYY-MM-DD")

    def test_reject_bad_time(self):
        self.assertEqual(_parse_local_inputs("2026-09-01", "10"), "时间格式应为 HH:MM")

    def test_reject_future(self):
        future = datetime.now().astimezone() + timedelta(days=1)
        got = _parse_local_inputs(future.strftime("%Y-%m-%d"), future.strftime("%H:%M"))
        self.assertEqual(got, "不能选择未来时间")

    def test_default_fields_without_applied_time(self):
        job_ref = MagicMock()
        job_ref.applied_observation_time = None
        date_text, time_text = _default_local_fields(job_ref)
        datetime.strptime(date_text, "%Y-%m-%d")
        datetime.strptime(time_text, "%H:%M")


if __name__ == "__main__":
    unittest.main()
