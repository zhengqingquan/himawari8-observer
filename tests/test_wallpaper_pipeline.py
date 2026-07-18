"""Seam: run_wallpaper_pipeline — adapters run in order; default grade is 4d."""

import time
import unittest
from pathlib import Path

from src.wallpaper_pipeline import run_wallpaper_pipeline


class RunWallpaperPipelineTests(unittest.TestCase):
    def test_runs_adapters_in_order_with_default_4d(self):
        events = []

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append(("download", pic.str_equal))

        def compose_equal(pic):
            events.append(("compose", pic.str_equal))

        def set_wallpaper(path: Path):
            events.append(("set", path.name))

        run_wallpaper_pipeline(
            fetch_observation_time=fetch_observation_time,
            download_tiles=download_tiles,
            compose_equal=compose_equal,
            set_wallpaper=set_wallpaper,
        )

        self.assertEqual(
            events,
            [
                "fetch",
                ("download", "4d"),
                ("compose", "4d"),
                ("set", "4d20210603052000.png"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
