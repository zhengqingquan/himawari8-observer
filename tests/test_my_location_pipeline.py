"""Pipeline my-location marker: on when enabled; skipped when off."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.wallpaper.pipeline import run_wallpaper_pipeline
from tests.workdir_paths import temporary_base_dir


class MyLocationMarkerPipelineTests(unittest.TestCase):
    def test_enabled_fetches_and_draws(self):
        draws = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(pic.final_path_equal)

        def set_wallpaper(path: Path):
            return True

        def fetch_ip():
            return (31.23, 121.47)

        def fake_draw(image_path, xy, **kwargs):
            draws.append((Path(image_path).name, xy, kwargs.get("label"), kwargs.get("color")))
            return True

        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                run_wallpaper_pipeline(
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_ip_latlon_fn=fetch_ip,
                    show_my_location=True,
                    cleanup_after_apply=False,
                    base_dir=base_dir,
                )

        self.assertEqual(len(draws), 1)
        self.assertEqual(draws[0][0], "4d20210603052000.png")
        self.assertEqual(draws[0][2], "ME")
        self.assertEqual(draws[0][3], (64, 156, 255))

    def test_disabled_does_not_fetch(self):
        fetch_calls = []

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

        def fetch_ip():
            fetch_calls.append(1)
            return (31.23, 121.47)

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                fetch_ip_latlon_fn=fetch_ip,
                show_my_location=False,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(fetch_calls, [])

    def test_toggle_on_uses_cache_without_network(self):
        downloads = []
        draws = []
        fetches = []
        ip_fetches = []

        def fetch_observation_time():
            fetches.append(1)
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(1)
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(pic.final_path_equal)

        def set_wallpaper(path: Path):
            return True

        def fetch_ip():
            ip_fetches.append(1)
            return (31.23, 121.47)

        def fake_draw(image_path, xy, **kwargs):
            draws.append(xy)
            return True

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_ip_latlon_fn=fetch_ip,
                    show_my_location=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                self.assertEqual(downloads, [1])
                self.assertEqual(ip_fetches, [1])
                self.assertTrue(state["last"][7])
                self.assertIn("my_location_cache", state)

                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_ip_latlon_fn=fetch_ip,
                    show_my_location=False,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                self.assertFalse(state["last"][7])

                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_ip_latlon_fn=fetch_ip,
                    show_my_location=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(downloads, [1])
        self.assertEqual(fetches, [1], "my-location toggle must not fetch latest.json")
        self.assertEqual(ip_fetches, [1], "re-enable must reuse my_location_cache")
        self.assertEqual(len(draws), 2)
        self.assertTrue(state["last"][7])

    def test_first_toggle_on_fetches_ip_on_fast_path(self):
        """首次开启无缓存时，快路径应联网拉 IP（不下载瓦片）。"""
        downloads = []
        draws = []
        fetches = []
        ip_fetches = []

        def fetch_observation_time():
            fetches.append(1)
            raise RuntimeError("latest.json must not be fetched on my-location toggle")

        def download_tiles(pic):
            downloads.append(1)

        def set_wallpaper(path: Path):
            return True

        def fetch_ip():
            ip_fetches.append(1)
            return (31.23, 121.47)

        def fake_draw(image_path, xy, **kwargs):
            draws.append(kwargs.get("label"))
            return True

        with temporary_base_dir() as base_dir:
            complete = Path(base_dir) / "img" / "20210603052000" / "complete"
            complete.mkdir(parents=True)
            wall = complete / "4d20210603052000.png"
            base = complete / "4d20210603052000_base.png"
            Image.new("RGB", (64, 64), (1, 2, 3)).save(wall)
            Image.new("RGB", (64, 64), (1, 2, 3)).save(base)
            state = {
                "last": ("2021-06-03 05:20:00", "4d", False, 0.0, 5.0, False, False, False),
                "wallpaper_path": str(wall),
                "wallpaper_base_path": str(base),
            }
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                result = run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=lambda pic: None,
                    set_wallpaper=set_wallpaper,
                    fetch_ip_latlon_fn=fetch_ip,
                    show_my_location=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertEqual(downloads, [])
        self.assertEqual(fetches, [])
        self.assertEqual(ip_fetches, [1])
        self.assertEqual(draws, ["ME"])
        self.assertIn("my_location_cache", state)
        self.assertTrue(state["last"][7])


if __name__ == "__main__":
    unittest.main()
