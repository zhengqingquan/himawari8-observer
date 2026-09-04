"""Pipeline sunglint marker: on when enabled; skipped when off."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.wallpaper.fingerprint import PostprocessOptions
from src.wallpaper.pipeline import run_wallpaper_pipeline
from tests.workdir_paths import temporary_base_dir


class SunglintMarkerPipelineTests(unittest.TestCase):
    def test_enabled_draws_sg(self):
        draws = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def set_wallpaper(path: Path):
            return True

        def fake_draw(image_path, xy, **kwargs):
            draws.append(
                (Path(image_path).name, kwargs.get("label"), kwargs.get("color"))
            )
            return True

        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                run_wallpaper_pipeline(
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    options=PostprocessOptions(show_sunglint_point=True),
                    cleanup_after_apply=False,
                    base_dir=base_dir,
                )

        self.assertEqual(len(draws), 1)
        self.assertEqual(draws[0][1], "SG")
        self.assertEqual(draws[0][2], (100, 220, 255))

    def test_disabled_does_not_draw(self):
        draws = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

        def set_wallpaper(path: Path):
            return True

        def fake_draw(*_args, **_kwargs):
            draws.append(1)
            return True

        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                run_wallpaper_pipeline(
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    options=PostprocessOptions(show_sunglint_point=False),
                    cleanup_after_apply=False,
                    base_dir=base_dir,
                )

        self.assertEqual(draws, [])


if __name__ == "__main__":
    unittest.main()
