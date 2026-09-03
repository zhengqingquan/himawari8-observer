"""Seam: download_files calls injectable per-tile downloader and updates status."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.download.pool import _build_session, download_files


class DownloadFilesTests(unittest.TestCase):
    def test_calls_download_one_and_marks_success(self):
        calls = []

        def fake_download_one(url, path):
            calls.append((url, str(path)))

        with tempfile.TemporaryDirectory() as tmp:
            a = str(Path(tmp) / "a.png")
            b = str(Path(tmp) / "b.png")
            urls = {
                "https://example.test/a.png": [a, 0],
                "https://example.test/b.png": [b, 0],
            }
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(
                sorted(calls),
                [
                    ("https://example.test/a.png", a),
                    ("https://example.test/b.png", b),
                ],
            )
            self.assertEqual(urls["https://example.test/a.png"][1], 1)
            self.assertEqual(urls["https://example.test/b.png"][1], 1)

    def test_failed_download_leaves_status_zero(self):
        calls = []

        def boom(url, path):
            calls.append(url)
            raise RuntimeError("network")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "a.png")
            urls = {"https://example.test/a.png": [path, 0]}
            download_files(urls, download_one=boom, retry_rounds=2)
            self.assertEqual(urls["https://example.test/a.png"][1], 0)
            self.assertEqual(len(calls), 3)  # pass-1 + 2 retries

    def test_failed_tiles_retried_until_success(self):
        attempts = {"https://example.test/a.png": 0}

        def flaky(url, path):
            attempts[url] += 1
            if attempts[url] < 3:
                raise RuntimeError("transient")
            Path(path).write_bytes(b"ok")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "a.png")
            urls = {"https://example.test/a.png": [path, 0]}
            download_files(urls, download_one=flaky, retry_rounds=2)
            self.assertEqual(urls["https://example.test/a.png"][1], 1)
            self.assertEqual(attempts["https://example.test/a.png"], 3)

    def test_retry_rounds_zero_does_not_retry(self):
        calls = []

        def boom(url, path):
            calls.append(url)
            raise RuntimeError("network")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "a.png")
            urls = {"https://example.test/a.png": [path, 0]}
            download_files(urls, download_one=boom, retry_rounds=0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(urls["https://example.test/a.png"][1], 0)

    def test_skips_existing_nonempty_file(self):
        calls = []

        def fake_download_one(url, path):
            calls.append(url)

        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "a.png"
            existing.write_bytes(b"png")
            missing = Path(tmp) / "b.png"
            urls = {
                "https://example.test/a.png": [str(existing), 0],
                "https://example.test/b.png": [str(missing), 0],
            }
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(calls, ["https://example.test/b.png"])
            self.assertEqual(urls["https://example.test/a.png"][1], 1)
            self.assertEqual(urls["https://example.test/b.png"][1], 1)

    def test_empty_existing_file_is_redownloaded(self):
        calls = []

        def fake_download_one(url, path):
            calls.append(url)
            Path(path).write_bytes(b"x")

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "a.png"
            empty.write_bytes(b"")
            urls = {"https://example.test/a.png": [str(empty), 0]}
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(calls, ["https://example.test/a.png"])
            self.assertEqual(urls["https://example.test/a.png"][1], 1)


class BuildSessionTests(unittest.TestCase):
    def test_pool_size_matches_workers(self):
        session = _build_session(pool_size=16)
        adapter = session.get_adapter("https://")
        self.assertEqual(adapter._pool_connections, 16)
        self.assertEqual(adapter._pool_maxsize, 16)


if __name__ == "__main__":
    unittest.main()
