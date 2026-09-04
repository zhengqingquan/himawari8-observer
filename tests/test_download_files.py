"""Seam: download_files calls injectable per-tile downloader and updates status."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.download.pool import _PNG_MAGIC, _build_session, download_file, download_files

from src.pic import TileSlot


class DownloadFilesTests(unittest.TestCase):
    def test_calls_download_one_and_marks_success(self):
        calls = []

        def fake_download_one(url, path):
            calls.append((url, str(path)))

        with tempfile.TemporaryDirectory() as tmp:
            a = str(Path(tmp) / "a.png")
            b = str(Path(tmp) / "b.png")
            urls = {
                "https://example.test/a.png": TileSlot(a),
                "https://example.test/b.png": TileSlot(b),
            }
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(
                sorted(calls),
                [
                    ("https://example.test/a.png", a),
                    ("https://example.test/b.png", b),
                ],
            )
            self.assertTrue(urls["https://example.test/a.png"].done)
            self.assertTrue(urls["https://example.test/b.png"].done)

    def test_failed_download_leaves_status_zero(self):
        calls = []

        def boom(url, path):
            calls.append(url)
            raise RuntimeError("network")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "a.png")
            urls = {"https://example.test/a.png": TileSlot(path)}
            download_files(urls, download_one=boom, retry_rounds=2)
            self.assertFalse(urls["https://example.test/a.png"].done)
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
            urls = {"https://example.test/a.png": TileSlot(path)}
            download_files(urls, download_one=flaky, retry_rounds=2)
            self.assertTrue(urls["https://example.test/a.png"].done)
            self.assertEqual(attempts["https://example.test/a.png"], 3)

    def test_retry_rounds_zero_does_not_retry(self):
        calls = []

        def boom(url, path):
            calls.append(url)
            raise RuntimeError("network")

        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "a.png")
            urls = {"https://example.test/a.png": TileSlot(path)}
            download_files(urls, download_one=boom, retry_rounds=0)
            self.assertEqual(len(calls), 1)
            self.assertFalse(urls["https://example.test/a.png"].done)

    def test_skips_existing_png_file(self):
        calls = []

        def fake_download_one(url, path):
            calls.append(url)

        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "a.png"
            existing.write_bytes(_PNG_MAGIC + b"rest")
            missing = Path(tmp) / "b.png"
            urls = {
                "https://example.test/a.png": TileSlot(str(existing)),
                "https://example.test/b.png": TileSlot(str(missing)),
            }
            with self.assertLogs(level="INFO") as captured:
                download_files(urls, download_one=fake_download_one)
            messages = "\n".join(captured.output)
            self.assertIn("Skipped 1 existing tile(s)", messages)
            self.assertIn("Tile download pass-1: 1 ok, 0 failed (of 1)", messages)
            self.assertEqual(calls, ["https://example.test/b.png"])
            self.assertTrue(urls["https://example.test/a.png"].done)
            self.assertTrue(urls["https://example.test/b.png"].done)

    def test_empty_existing_file_is_redownloaded(self):
        calls = []

        def fake_download_one(url, path):
            calls.append(url)
            Path(path).write_bytes(_PNG_MAGIC)

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "a.png"
            empty.write_bytes(b"")
            urls = {"https://example.test/a.png": TileSlot(str(empty))}
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(calls, ["https://example.test/a.png"])
            self.assertTrue(urls["https://example.test/a.png"].done)

    def test_non_png_existing_file_is_redownloaded(self):
        calls = []

        def fake_download_one(url, path):
            calls.append(url)
            Path(path).write_bytes(_PNG_MAGIC)

        with tempfile.TemporaryDirectory() as tmp:
            garbage = Path(tmp) / "a.png"
            garbage.write_bytes(b"half-written-garbage")
            urls = {"https://example.test/a.png": TileSlot(str(garbage))}
            download_files(urls, download_one=fake_download_one)
            self.assertEqual(calls, ["https://example.test/a.png"])
            self.assertTrue(urls["https://example.test/a.png"].done)
            self.assertTrue(garbage.read_bytes().startswith(_PNG_MAGIC))


class DownloadFileAtomicTests(unittest.TestCase):
    def test_writes_via_part_then_replace(self):
        payload = _PNG_MAGIC + b"tile-body"

        class _Resp:
            def raise_for_status(self):
                return None

            def iter_content(self, chunk_size=8192):
                yield payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        session = MagicMock()
        session.get.return_value = _Resp()

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "a.png"
            name = download_file("https://example.test/a.png", dest, session=session)
            self.assertEqual(name, "a.png")
            self.assertEqual(dest.read_bytes(), payload)
            self.assertFalse(dest.with_name("a.png.part").exists())

    def test_failed_stream_leaves_no_final_or_part(self):
        class _Resp:
            def raise_for_status(self):
                return None

            def iter_content(self, chunk_size=8192):
                yield _PNG_MAGIC
                raise ConnectionError("cut mid-stream")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        session = MagicMock()
        session.get.return_value = _Resp()

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "a.png"
            with self.assertRaises(ConnectionError):
                download_file("https://example.test/a.png", dest, session=session)
            self.assertFalse(dest.exists())
            self.assertFalse(dest.with_name("a.png.part").exists())


class BuildSessionTests(unittest.TestCase):
    def test_pool_size_matches_workers(self):
        session = _build_session(pool_size=16)
        adapter = session.get_adapter("https://")
        self.assertEqual(adapter._pool_connections, 16)
        self.assertEqual(adapter._pool_maxsize, 16)


if __name__ == "__main__":
    unittest.main()
