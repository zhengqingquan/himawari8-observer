"""Seam: download_files calls injectable per-tile downloader."""

import unittest

from src.dl_thread.dl_thread import download_files


class DownloadFilesTests(unittest.TestCase):
    def test_calls_download_one_for_each_url(self):
        calls = []

        def fake_download_one(url, path):
            calls.append((url, str(path)))

        urls = {
            "https://example.test/a.png": ["/tmp/a.png", 0],
            "https://example.test/b.png": ["/tmp/b.png", 0],
        }
        download_files(urls, download_one=fake_download_one)
        self.assertEqual(
            sorted(calls),
            [
                ("https://example.test/a.png", "/tmp/a.png"),
                ("https://example.test/b.png", "/tmp/b.png"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
