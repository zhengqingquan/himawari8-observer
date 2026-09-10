"""Observation time fetch from latest.json and yesterday-local / local slot."""

from __future__ import annotations

import json
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.download.observation import (
    fetch_observation_time,
    floor_datetime_to_full_disk_utc,
    observation_time_from_local,
    observation_time_yesterday_local,
)


class FetchObservationTimeTests(unittest.TestCase):
    def test_parses_date_from_latest_json(self):
        session = MagicMock()
        response = MagicMock()
        response.content = json.dumps({"date": "2026-09-03 02:10:00"}).encode("utf-8")
        response.raise_for_status.return_value = None
        session.get.return_value = response

        got = fetch_observation_time(session)
        self.assertEqual(got, time.strptime("2026-09-03 02:10:00", "%Y-%m-%d %H:%M:%S"))
        session.get.assert_called_once()
        url = session.get.call_args.args[0]
        self.assertEqual(url, "https://himawari8.nict.go.jp/img/D531106/latest.json")

    def test_http_error_propagates(self):
        session = MagicMock()
        response = MagicMock()
        response.raise_for_status.side_effect = RuntimeError("http 500")
        session.get.return_value = response

        with self.assertRaises(RuntimeError):
            fetch_observation_time(session)


class ObservationTimeYesterdayLocalTests(unittest.TestCase):
    def test_beijing_1722_maps_to_utc_0920_previous_day(self):
        china = timezone(timedelta(hours=8))
        now = datetime(2026, 9, 3, 17, 22, tzinfo=china)
        got = observation_time_yesterday_local(now=now)
        self.assertEqual(got, time.strptime("2026-09-02 09:20:00", "%Y-%m-%d %H:%M:%S"))

    def test_exact_ten_minute_boundary_unchanged(self):
        china = timezone(timedelta(hours=8))
        now = datetime(2026, 9, 3, 17, 20, tzinfo=china)
        got = observation_time_yesterday_local(now=now)
        self.assertEqual(got, time.strptime("2026-09-02 09:20:00", "%Y-%m-%d %H:%M:%S"))


class ObservationTimeFromLocalTests(unittest.TestCase):
    def test_beijing_1722_floors_to_utc_0920(self):
        china = timezone(timedelta(hours=8))
        local = datetime(2026, 9, 3, 17, 22, tzinfo=china)
        got = observation_time_from_local(local)
        self.assertEqual(got, time.strptime("2026-09-03 09:20:00", "%Y-%m-%d %H:%M:%S"))

    def test_floor_helper_zeros_seconds(self):
        china = timezone(timedelta(hours=8))
        local = datetime(2026, 9, 3, 17, 29, 59, tzinfo=china)
        floored = floor_datetime_to_full_disk_utc(local)
        self.assertEqual(floored, datetime(2026, 9, 3, 9, 20, 0, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
