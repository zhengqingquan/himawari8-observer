"""Pipeline typhoon marker: on when enabled; skipped when off."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.wallpaper.pipeline import run_wallpaper_pipeline
from tests.workdir_paths import temporary_base_dir


class TyphoonMarkerPipelineTests(unittest.TestCase):
    def test_enabled_fetches_and_draws(self):
        draws = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry[1] = 1

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def set_wallpaper(path: Path):
            return True

        def fetch_center(_obs):
            return (29.024, 128.437)

        def fake_draw(image_path, xy, **kwargs):
            draws.append((Path(image_path).name, xy))
            return True

        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.pipeline.draw_typhoon_marker", side_effect=fake_draw):
                run_wallpaper_pipeline(
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    base_dir=base_dir,
                )

        self.assertEqual(len(draws), 1)
        self.assertEqual(draws[0][0], "4d20210603052000.png")
        self.assertIsInstance(draws[0][1], tuple)

    def test_disabled_does_not_fetch(self):
        fetch_calls = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry[1] = 1

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

        def set_wallpaper(path: Path):
            return True

        def fetch_center(_obs):
            fetch_calls.append(1)
            return (29.024, 128.437)

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                fetch_typhoon_center_fn=fetch_center,
                show_typhoon_marker=False,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(fetch_calls, [])


if __name__ == "__main__":
    unittest.main()
