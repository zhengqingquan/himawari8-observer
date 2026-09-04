"""fetch_typhoon_center: TY / non-TY / 404."""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock

from src.download.typhoon import fetch_typhoon_center, typhoon_json_url


class TyphoonFetchTests(unittest.TestCase):
    def setUp(self):
        self.obs = time.strptime("2026-09-04 00:30:00", "%Y-%m-%d %H:%M:%S")

    def test_url_matches_observation_time(self):
        self.assertEqual(
            typhoon_json_url(self.obs),
            "https://himawari8.nict.go.jp/json/D531108/2026/09/04/003000.json",
        )

    def test_returns_center_for_ty(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"type": "TY", "center": [29.024, 128.437]}
        session.get.return_value = response

        self.assertEqual(fetch_typhoon_center(self.obs, session=session), (29.024, 128.437))

    def test_returns_none_for_non_ty(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"type": "OTHER"}
        session.get.return_value = response

        self.assertIsNone(fetch_typhoon_center(self.obs, session=session))

    def test_returns_none_for_404(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 404
        session.get.return_value = response

        self.assertIsNone(fetch_typhoon_center(self.obs, session=session))


if __name__ == "__main__":
    unittest.main()
