"""JTWC ABPW INVEST parsing."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.download.jtwc import fetch_jtwc_invests, parse_jtwc_invests

_SAMPLE_ABPW = """
ABPW10 PGTW 040630
1. WESTERN NORTH PACIFIC AREA (180 TO MALAY PENINSULA):
   A. TROPICAL CYCLONE SUMMARY:
      (1) AT 04SEP26 0000Z, TROPICAL STORM 22W (KROVANH) WAS LOCATED
NEAR 29.5N 128.0E, APPROXIMATELY 180 NM NORTH OF KADENA AB.
      (2) NO OTHER TROPICAL CYCLONES.
   B. TROPICAL DISTURBANCE SUMMARY:
      (1)  THE AREA OF CONVECTION (INVEST 97W) PREVIOUSLY LOCATED
NEAR 17.6N 138.9E IS NOW LOCATED NEAR 19.2N 138.3E, APPROXIMATELY 370
NM SOUTH-SOUTHWEST OF IWO TO, JAPAN.
      (2) NO OTHER SUSPECT AREAS.
2. SOUTH PACIFIC AREA (WEST COAST OF SOUTH AMERICA TO 135 EAST):
   A. TROPICAL CYCLONE SUMMARY: NONE.
"""


class JtwcInvestParseTests(unittest.TestCase):
    def test_parses_invest_now_located_near(self):
        invests = parse_jtwc_invests(_SAMPLE_ABPW)
        self.assertEqual(invests, [{"id": "97W", "lat": 19.2, "lon": 138.3}])

    def test_ignores_named_tropical_storm(self):
        invests = parse_jtwc_invests(_SAMPLE_ABPW)
        ids = [item["id"] for item in invests]
        self.assertNotIn("22W", ids)

    def test_empty_when_no_invest(self):
        text = """
1. WESTERN NORTH PACIFIC AREA:
   A. TROPICAL CYCLONE SUMMARY:
      (1) AT 04SEP26 0000Z, TYPHOON 22W (KROVANH) WAS LOCATED NEAR 29.5N 128.0E
      (2) NO OTHER TROPICAL CYCLONES.
   B. TROPICAL DISTURBANCE SUMMARY:
      (1) NO OTHER SUSPECT AREAS.
2. SOUTH PACIFIC AREA:
   A. TROPICAL CYCLONE SUMMARY: NONE.
"""
        self.assertEqual(parse_jtwc_invests(text), [])

    def test_fetch_returns_parsed_list(self):
        session = MagicMock()
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.text = _SAMPLE_ABPW
        session.get.return_value = response
        self.assertEqual(
            fetch_jtwc_invests(session=session),
            [{"id": "97W", "lat": 19.2, "lon": 138.3}],
        )


if __name__ == "__main__":
    unittest.main()
