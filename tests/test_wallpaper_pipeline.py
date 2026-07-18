"""Seam: run_wallpaper_pipeline — adapters, default grade, download completeness gate."""

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
            for entry in pic.dic.values():
                entry[1] = 1

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

    def test_skips_compose_when_tiles_incomplete(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")
            # leave all status bits at 0

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append("set")

        run_wallpaper_pipeline(
            fetch_observation_time=fetch_observation_time,
            download_tiles=download_tiles,
            compose_equal=compose_equal,
            set_wallpaper=set_wallpaper,
        )

        self.assertEqual(events, ["download"])


if __name__ == "__main__":
    unittest.main()
