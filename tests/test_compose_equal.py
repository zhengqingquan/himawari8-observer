"""Equal-tile compose closes tile images promptly."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from src.compose.equal import apply_margins, compose_equal_image


class ComposeEqualImageTests(unittest.TestCase):
    def test_composes_2x2_tiles_and_closes_canvas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tiles = {}
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            for index, color in enumerate(colors):
                path = root / f"{index}.png"
                Image.new("RGB", (10, 10), color=color).save(path)
                tiles[f"url-{index}"] = [str(path), 1]

            out = root / "out.png"
            pic = SimpleNamespace(
                pic_side=20,
                pic_pixel=10,
                grid_size=2,
                grade="2d",
                final_path_equal=out,
                tiles=tiles,
            )
            compose_equal_image(pic)
            self.assertTrue(out.is_file())
            with Image.open(out) as composed:
                self.assertEqual(composed.size, (20, 20))
                self.assertEqual(composed.getpixel((0, 0)), (255, 0, 0))
                self.assertEqual(composed.getpixel((10, 0)), (0, 255, 0))
                self.assertEqual(composed.getpixel((0, 10)), (0, 0, 255))
                self.assertEqual(composed.getpixel((10, 10)), (255, 255, 0))


class ApplyMarginsTests(unittest.TestCase):
    def test_saves_margin_canvas_and_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.png"
            out = Path(tmp) / "out.png"
            Image.new("RGB", (100, 100), color=(10, 20, 30)).save(src)
            with patch("src.compose.equal.ImageGrab.grab") as grab:
                grab.return_value = SimpleNamespace(size=(200, 100))
                apply_margins(
                    str(src),
                    100,
                    str(out),
                    top_percent=0.0,
                    bottom_percent=0.0,
                )
            self.assertTrue(out.is_file())
            with Image.open(out) as result:
                self.assertEqual(result.size, (200, 100))


if __name__ == "__main__":
    unittest.main()
