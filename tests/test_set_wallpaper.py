"""Desktop wallpaper path helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.set_wallpaper import get_desktop_wallpaper, set_wallpaper, wallpaper_paths_match


class WallpaperPathsMatchTests(unittest.TestCase):
    def test_same_resolved_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            path.write_bytes(b"x")
            self.assertTrue(wallpaper_paths_match(path, path.resolve()))

    def test_rejects_empty_or_different(self):
        self.assertFalse(wallpaper_paths_match(None, r"C:\a.png"))
        self.assertFalse(wallpaper_paths_match(r"C:\a.png", r"C:\b.png"))


class GetDesktopWallpaperTests(unittest.TestCase):
    def test_returns_path_from_system_parameters(self):
        def fake_spi(action, buf_len, buf, flags):
            buf.value = r"C:\Wallpapers\earth.png"
            return 1

        with patch(
            "src.set_wallpaper.ctypes.windll.user32.SystemParametersInfoW",
            side_effect=fake_spi,
        ):
            self.assertEqual(get_desktop_wallpaper(), r"C:\Wallpapers\earth.png")

    def test_returns_none_when_api_fails(self):
        with patch(
            "src.set_wallpaper.ctypes.windll.user32.SystemParametersInfoW",
            return_value=0,
        ):
            self.assertIsNone(get_desktop_wallpaper())


class SetWallpaperTests(unittest.TestCase):
    def test_missing_file_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.png"
            self.assertFalse(set_wallpaper(missing))

    def test_calls_system_parameters_for_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wall.png"
            path.write_bytes(b"png")
            with patch(
                "src.set_wallpaper.ctypes.windll.user32.SystemParametersInfoW",
                return_value=1,
            ) as spi:
                self.assertTrue(set_wallpaper(path))
                spi.assert_called_once()
                args = spi.call_args[0]
                self.assertEqual(args[0], 20)
                self.assertEqual(args[3], 1)

    def test_api_failure_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wall.png"
            path.write_bytes(b"png")
            with patch(
                "src.set_wallpaper.ctypes.windll.user32.SystemParametersInfoW",
                return_value=0,
            ):
                self.assertFalse(set_wallpaper(path))


if __name__ == "__main__":
    unittest.main()
