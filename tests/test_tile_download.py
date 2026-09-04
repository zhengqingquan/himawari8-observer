"""Seam: download_tiles is the sole live tile-download entry."""

import time
import unittest

from src.download.tiles import download_tiles
from src.pic import Pic
from tests.workdir_paths import temporary_base_dir


class TileDownloadTests(unittest.TestCase):
    def test_download_tiles_delegates_to_impl_and_can_finish(self):
        pic_time = time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")
        with temporary_base_dir() as base_dir:
            pic = Pic(pic_time, "1d", base_dir=base_dir)
            seen = []

            def fake_download_files(urls, **_kwargs):
                seen.append(len(urls))
                for entry in urls.values():
                    entry.done = True

            download_tiles(pic, download_files_impl=fake_download_files)
            self.assertEqual(seen, [1])
            self.assertTrue(pic.download_finish())


if __name__ == "__main__":
    unittest.main()
