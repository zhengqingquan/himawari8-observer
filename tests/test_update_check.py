"""Unit tests for GitHub release update check."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from src.update_check import (
    UpdateStatus,
    check_for_update,
    compare_versions,
    fetch_latest_release_tag,
    normalize_version,
)


class NormalizeVersionTests(unittest.TestCase):
    def test_strips_v_prefix(self):
        self.assertEqual(normalize_version("v1.3.1"), (1, 3, 1))
        self.assertEqual(normalize_version("V2.0.0"), (2, 0, 0))
        self.assertEqual(normalize_version("1.2.3"), (1, 2, 3))

    def test_rejects_invalid(self):
        with self.assertRaises(ValueError):
            normalize_version("")
        with self.assertRaises(ValueError):
            normalize_version("v")
        with self.assertRaises(ValueError):
            normalize_version("1.x.0")


class CompareVersionsTests(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(compare_versions("v1.3.1", "1.3.1"), 0)

    def test_behind(self):
        self.assertEqual(compare_versions("v1.3.0", "v1.3.1"), -1)

    def test_ahead(self):
        self.assertEqual(compare_versions("v1.4.0", "v1.3.1"), 1)

    def test_pads_shorter(self):
        self.assertEqual(compare_versions("v1.3", "v1.3.0"), 0)
        self.assertEqual(compare_versions("v1.3", "v1.3.1"), -1)


class FetchLatestReleaseTagTests(unittest.TestCase):
    def test_success(self):
        response = MagicMock()
        response.json.return_value = {"tag_name": "v1.4.0"}
        response.raise_for_status.return_value = None
        session = MagicMock()
        session.get.return_value = response

        self.assertEqual(fetch_latest_release_tag(session=session), "v1.4.0")
        session.get.assert_called_once()

    def test_http_error(self):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError("404")
        session = MagicMock()
        session.get.return_value = response

        with self.assertRaises(requests.HTTPError):
            fetch_latest_release_tag(session=session)

    def test_missing_tag_name(self):
        response = MagicMock()
        response.json.return_value = {}
        response.raise_for_status.return_value = None
        session = MagicMock()
        session.get.return_value = response

        with self.assertRaises(ValueError):
            fetch_latest_release_tag(session=session)


class CheckForUpdateTests(unittest.TestCase):
    @patch("src.update_check.fetch_latest_release_tag", return_value="v1.3.1")
    def test_up_to_date(self, _mock_fetch):
        result = check_for_update(current_version="v1.3.1")
        self.assertIs(result.status, UpdateStatus.UP_TO_DATE)
        self.assertEqual(result.latest_version, "v1.3.1")

    @patch("src.update_check.fetch_latest_release_tag", return_value="v1.4.0")
    def test_update_available(self, _mock_fetch):
        result = check_for_update(current_version="v1.3.1")
        self.assertIs(result.status, UpdateStatus.UPDATE_AVAILABLE)
        self.assertEqual(result.latest_version, "v1.4.0")

    @patch("src.update_check.fetch_latest_release_tag", return_value="v1.2.0")
    def test_local_ahead_counts_as_up_to_date(self, _mock_fetch):
        result = check_for_update(current_version="v1.3.1")
        self.assertIs(result.status, UpdateStatus.UP_TO_DATE)

    @patch(
        "src.update_check.fetch_latest_release_tag",
        side_effect=requests.Timeout("timed out"),
    )
    def test_timeout_failed(self, _mock_fetch):
        result = check_for_update(current_version="v1.3.1")
        self.assertIs(result.status, UpdateStatus.FAILED)
        self.assertIsNone(result.latest_version)


if __name__ == "__main__":
    unittest.main()
