"""IP geolocation fetch: parse success / failure."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from src.download.geoip import fetch_ip_latlon


class FetchIpLatlonTests(unittest.TestCase):
    def test_success_returns_lat_lon(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "success": True,
            "latitude": 31.23,
            "longitude": 121.47,
        }
        session = MagicMock()
        session.get.return_value = response

        result = fetch_ip_latlon(session=session)

        self.assertEqual(result, (31.23, 121.47))
        session.get.assert_called_once()

    def test_missing_coords_returns_none(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"success": True, "latitude": 31.23}
        session = MagicMock()
        session.get.return_value = response

        self.assertIsNone(fetch_ip_latlon(session=session))

    def test_api_failure_flag_returns_none(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"success": False, "message": "reserved range"}
        session = MagicMock()
        session.get.return_value = response

        self.assertIsNone(fetch_ip_latlon(session=session))

    def test_request_error_returns_none(self):
        session = MagicMock()
        session.get.side_effect = requests.RequestException("timeout")

        with patch("src.download.geoip.logging"):
            self.assertIsNone(fetch_ip_latlon(session=session))

    def test_out_of_range_returns_none(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "success": True,
            "latitude": 999.0,
            "longitude": 121.0,
        }
        session = MagicMock()
        session.get.return_value = response

        self.assertIsNone(fetch_ip_latlon(session=session))


if __name__ == "__main__":
    unittest.main()
