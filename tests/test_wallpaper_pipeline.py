"""Seam: run_wallpaper_pipeline — adapters, default grade, download completeness gate."""

import time
import unittest
from pathlib import Path

from src.wallpaper.pipeline import run_wallpaper_pipeline
from tests.workdir_paths import temporary_base_dir


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

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                base_dir=base_dir,
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

    def test_auto_adjust_runs_before_set_wallpaper(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.dic.values():
                entry[1] = 1

        def compose_equal(pic):
            events.append("compose")

        def adjust_wallpaper(pic):
            events.append("adjust")
            return Path(pic.final_path_equal).with_name("adjusted.png")

        def set_wallpaper(path: Path):
            events.append(("set", path.name))

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                adjust_wallpaper=adjust_wallpaper,
                set_wallpaper=set_wallpaper,
                auto_adjust=True,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(events, ["compose", "adjust", ("set", "adjusted.png")])

    def test_skips_adjust_when_auto_adjust_false(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.dic.values():
                entry[1] = 1

        def compose_equal(pic):
            events.append("compose")

        def adjust_wallpaper(pic):
            events.append("adjust")
            return Path("should_not_use.png")

        def set_wallpaper(path: Path):
            events.append(("set", path.name))

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                adjust_wallpaper=adjust_wallpaper,
                set_wallpaper=set_wallpaper,
                auto_adjust=False,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(events, ["compose", ("set", "4d20210603052000.png")])

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

        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(events, ["download"])

    def test_skips_when_applied_run_unchanged(self):
        events = []
        state = {"last": None}

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")
            for entry in pic.dic.values():
                entry[1] = 1

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append("set")
            return True

        with temporary_base_dir() as base_dir:
            kwargs = dict(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            run_wallpaper_pipeline(**kwargs)
            run_wallpaper_pipeline(**kwargs)

        self.assertEqual(
            events,
            ["fetch", "download", "compose", "set", "fetch"],
        )

    def test_reruns_when_observation_time_changes(self):
        events = []
        state = {"last": None}
        times = [
            time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S"),
            time.strptime("2021-06-03 05:30:00", "%Y-%m-%d %H:%M:%S"),
        ]

        def fetch_observation_time():
            return times.pop(0)

        def download_tiles(pic):
            events.append(("download", pic.folder_root))
            for entry in pic.dic.values():
                entry[1] = 1

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append(("set", path.name))
            return True

        with temporary_base_dir() as base_dir:
            kwargs = dict(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            run_wallpaper_pipeline(**kwargs)
            run_wallpaper_pipeline(**kwargs)

        self.assertEqual(
            events,
            [
                ("download", "20210603052000"),
                "compose",
                ("set", "4d20210603052000.png"),
                ("download", "20210603053000"),
                "compose",
                ("set", "4d20210603053000.png"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
