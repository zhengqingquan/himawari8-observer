"""Seam: Pic builds equal tile map without legacy complete-download fields."""

import tempfile
import time
import unittest
from pathlib import Path

from src.cls.Pic import Pic


class PicEqualOnlyTests(unittest.TestCase):
    def test_init_builds_tile_dic_only(self):
        pic_time = time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")
        pic = Pic(pic_time, "1d")
        self.assertEqual(len(pic.dic), 1)
        self.assertFalse(hasattr(pic, "post_data"))
        self.assertFalse(hasattr(pic, "pic_name_cpl"))
        self.assertFalse(hasattr(pic, "ensure_complete_download_fields"))
        self.assertFalse(hasattr(Pic, "sc_nc_web_base"))
        self.assertFalse(hasattr(Pic, "hash_base"))

    def test_base_dir_scopes_all_local_paths(self):
        pic_time = time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pic = Pic(pic_time, "2d", base_dir=base)
            self.assertEqual(pic.base_dir, base)
            self.assertTrue(str(pic.folder_path).startswith(str(base)))
            self.assertEqual(
                pic.final_path_equal,
                base / "img" / "20210603052000" / "complete" / "2d20210603052000.png",
            )
            for path, _status in pic.dic.values():
                self.assertTrue(str(path).startswith(str(base / "img")))


if __name__ == "__main__":
    unittest.main()
