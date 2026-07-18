"""Seam: Pic equal construction does not build complete-download fields."""

import time
import unittest

from src.cls.Pic import Pic


class PicCompleteLeakTests(unittest.TestCase):
    def setUp(self):
        self.pic_time = time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

    def test_init_does_not_build_complete_fields(self):
        pic = Pic(self.pic_time, "4d")
        self.assertEqual(pic.post_data, {})
        self.assertIsNone(pic.pic_name_cpl)
        self.assertIsNone(pic.final_path_cpl)
        self.assertTrue(pic.dic)  # equal path still built

    def test_ensure_complete_download_fields_fills_post_data(self):
        pic = Pic(self.pic_time, "4d")
        pic.ensure_complete_download_fields()
        self.assertEqual(pic.pic_name_cpl, "hima820210603052000fd.png")
        self.assertIsNotNone(pic.final_path_cpl)
        self.assertIn("filelist[0]", pic.post_data)
        self.assertTrue(str(pic.final_path_cpl).endswith(pic.pic_name_cpl))


if __name__ == "__main__":
    unittest.main()
