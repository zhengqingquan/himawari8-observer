"""Equal-tile compose closes tile images promptly."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from src.compose.equal import (
    apply_margins,
    compose_equal_image,
    compose_equal_image_with_margins,
    compute_margin_layout,
    get_primary_screen_size,
    reduce_color_banding,
)


class ComputeMarginLayoutTests(unittest.TestCase):
    def test_zero_margins_centers_on_wider_canvas(self):
        canvas_w, canvas_h, image_x, image_y = compute_margin_layout(
            100,
            200,
            100,
            top_percent=0.0,
            bottom_percent=0.0,
        )
        self.assertEqual((canvas_w, canvas_h), (200, 100))
        self.assertEqual((image_x, image_y), (50, 0))

    def test_top_and_bottom_percent_expand_height_and_offset(self):
        canvas_w, canvas_h, image_x, image_y = compute_margin_layout(
            100,
            100,
            100,
            top_percent=10.0,
            bottom_percent=20.0,
        )
        # content_height = 100 + 10 + 20 = 130; scale = 1.3; canvas_w = ceil(130)=130
        self.assertEqual(canvas_h, 130)
        self.assertEqual(canvas_w, 130)
        self.assertEqual(image_y, 10)
        self.assertEqual(image_x, 15)


class GetPrimaryScreenSizeTests(unittest.TestCase):
    def test_reads_system_metrics(self):
        with patch("src.compose.equal.ctypes.windll.user32.GetSystemMetrics") as metrics:
            metrics.side_effect = lambda index: {0: 1920, 1: 1080}[index]
            self.assertEqual(get_primary_screen_size(), (1920, 1080))

    def test_rejects_invalid_size(self):
        with patch("src.compose.equal.ctypes.windll.user32.GetSystemMetrics", return_value=0):
            with self.assertRaises(OSError):
                get_primary_screen_size()


class ReduceColorBandingTests(unittest.TestCase):
    def test_preserves_pure_black(self):
        src = Image.new("RGB", (32, 32), color=(0, 0, 0))
        try:
            out = reduce_color_banding(src)
            try:
                self.assertEqual(out.getpixel((0, 0)), (0, 0, 0))
                self.assertEqual(out.getpixel((16, 16)), (0, 0, 0))
            finally:
                out.close()
        finally:
            src.close()

    def test_breaks_flat_midtone_into_varied_pixels(self):
        src = Image.new("RGB", (64, 64), color=(40, 40, 48))
        try:
            out = reduce_color_banding(src)
            try:
                colors = {out.getpixel((x, y)) for x in range(0, 64, 4) for y in range(0, 64, 4)}
                self.assertGreater(len(colors), 1)
            finally:
                out.close()
        finally:
            src.close()

    def test_reduces_posterized_gradient_jumps(self):
        width, height = 320, 40
        src = Image.new("RGB", (width, height))
        pixels = src.load()
        for x in range(width):
            level = (x // 20) * 15
            for y in range(height):
                pixels[x, y] = (level, level, level)
        try:
            out = reduce_color_banding(src)
            try:
                before = [src.getpixel((x, height // 2))[0] for x in range(width)]
                after = [out.getpixel((x, height // 2))[0] for x in range(width)]
                self.assertGreater(len(set(before)), 5)
                self.assertGreater(len(set(after)), len(set(before)))
            finally:
                out.close()
        finally:
            src.close()


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
            compose_equal_image(pic, deband=False)
            self.assertTrue(out.is_file())
            with Image.open(out) as composed:
                self.assertEqual(composed.size, (20, 20))
                self.assertEqual(composed.getpixel((0, 0)), (255, 0, 0))
                self.assertEqual(composed.getpixel((10, 0)), (0, 255, 0))
                self.assertEqual(composed.getpixel((0, 10)), (0, 0, 255))
                self.assertEqual(composed.getpixel((10, 10)), (255, 255, 0))

    def test_composes_tiles_directly_onto_margin_canvas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tiles = {}
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            for index, color in enumerate(colors):
                path = root / f"{index}.png"
                Image.new("RGB", (10, 10), color=color).save(path)
                tiles[f"url-{index}"] = [str(path), 1]

            pic = SimpleNamespace(
                pic_side=20,
                pic_pixel=10,
                grid_size=2,
                grade="2d",
                tiles=tiles,
            )
            out = root / "adjusted.png"
            result = compose_equal_image_with_margins(
                pic,
                out,
                top_percent=0.0,
                bottom_percent=0.0,
                screen_size=(40, 20),
                deband=False,
            )
            self.assertEqual(result, out)
            with Image.open(out) as composed:
                self.assertEqual(composed.size, (40, 20))
                # content centered: offset x = 10
                self.assertEqual(composed.getpixel((10, 0)), (255, 0, 0))
                self.assertEqual(composed.getpixel((20, 0)), (0, 255, 0))
                self.assertEqual(composed.getpixel((0, 0)), (0, 0, 0))


class ApplyMarginsTests(unittest.TestCase):
    def test_saves_margin_canvas_and_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.png"
            out = Path(tmp) / "out.png"
            Image.new("RGB", (100, 100), color=(10, 20, 30)).save(src)
            apply_margins(
                str(src),
                100,
                str(out),
                top_percent=0.0,
                bottom_percent=0.0,
                screen_size=(200, 100),
                deband=False,
            )
            self.assertTrue(out.is_file())
            with Image.open(out) as result:
                self.assertEqual(result.size, (200, 100))


if __name__ == "__main__":
    unittest.main()
