"""Desktop wallpaper path helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.set_wallpaper import wallpaper_paths_match


class WallpaperPathsMatchTests(unittest.TestCase):
    def test_same_resolved_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(b"x")
            self.assertTrue(wallpaper_paths_match(path, path.resolve()))

    def test_rejects_empty_or_different(self):
        self.assertFalse(wallpaper_paths_match(None, r"C:\a.png"))
        self.assertFalse(wallpaper_paths_match(r"C:\a.png", r"C:\b.png"))


if __name__ == "__main__":
    unittest.main()
