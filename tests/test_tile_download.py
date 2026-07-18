"""Seam: download_tiles is the sole live tile-download entry."""

import time
import unittest

from src.cls.Pic import Pic
from src.tile_download import download_tiles


class TileDownloadTests(unittest.TestCase):
    def test_download_tiles_delegates_to_impl_and_can_finish(self):
        pic_time = time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")
        pic = Pic(pic_time, "1d")
        seen = []

        def fake_download_files(urls, **_kwargs):
            seen.append(len(urls))
            for entry in urls.values():
                entry[1] = 1

        download_tiles(pic, download_files_impl=fake_download_files)
        self.assertEqual(seen, [1])
        self.assertTrue(pic.download_finish())


if __name__ == "__main__":
    unittest.main()
