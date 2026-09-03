"""Observation time fetch from latest.json."""

from __future__ import annotations

import json
import time
import unittest
from unittest.mock import MagicMock

from src.download.observation import fetch_observation_time


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

    def test_http_error_propagates(self):
        session = MagicMock()
        response = MagicMock()
        response.raise_for_status.side_effect = RuntimeError("http 500")
        session.get.return_value = response

        with self.assertRaises(RuntimeError):
            fetch_observation_time(session)


if __name__ == "__main__":
    unittest.main()
