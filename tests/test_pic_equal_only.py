"""Seam: Pic builds equal tile map without legacy complete-download fields."""

import time
import unittest

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


if __name__ == "__main__":
    unittest.main()
