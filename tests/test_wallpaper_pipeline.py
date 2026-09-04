"""Seam: run_wallpaper_pipeline — adapters, default grade, download completeness gate."""

import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.wallpaper.pipeline import run_wallpaper_pipeline
from src.wallpaper.fingerprint import PostprocessOptions
from tests.workdir_paths import temporary_base_dir


class RunWallpaperPipelineTests(unittest.TestCase):
    def test_runs_adapters_in_order_with_default_4d(self):
        events = []

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append(("download", pic.grade))
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            events.append(("compose", pic.grade))

        def set_wallpaper(path: Path):
            events.append(("set", path.name))

        with temporary_base_dir() as base_dir:
            result = run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertEqual(
            events,
            [
                "fetch",
                ("download", "4d"),
                ("compose", "4d"),
                ("set", "4d20210603052000.png"),
            ],
        )

    def test_record_run_key_false_returns_time_without_fingerprint(self):
        state = {"last": None, "wallpaper_path": None}

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

        with temporary_base_dir() as base_dir:
            result = run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                applied_run_state=state,
                record_run_key=False,
                base_dir=base_dir,
            )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertIsNone(state["last"])
        self.assertEqual(state["applied_grade"], "4d")
        self.assertIsNotNone(state["wallpaper_path"])

    def test_auto_adjust_runs_before_set_wallpaper(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

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
                options=PostprocessOptions(auto_adjust=True),
                cleanup_after_apply=False,
                base_dir=base_dir,
            )

        self.assertEqual(events, ["compose", "adjust", ("set", "adjusted.png")])

    def test_default_auto_adjust_composes_equal_then_margins_and_keeps_disk(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

        def set_wallpaper(path: Path):
            events.append(("set", path.name))
            return True

        def fake_compose(pic, **_kwargs):
            events.append("compose")
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def fake_margins(file, margin, path, **_kwargs):
            events.append("margins")
            out = Path(path)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil_copy = __import__("shutil").copy2
            shutil_copy(file, out)

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            with (
                patch("src.wallpaper.pipeline.compose_equal_image", side_effect=fake_compose),
                patch("src.wallpaper.pipeline.apply_margins", side_effect=fake_margins),
            ):
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    set_wallpaper=set_wallpaper,
                    options=PostprocessOptions(auto_adjust=True),
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

            disk = Path(state["wallpaper_disk_path"])
            self.assertTrue(disk.is_file())
            self.assertTrue(disk.name.endswith("_disk.png"))

        self.assertEqual(
            events,
            ["compose", "margins", ("set", "4d20210603052000_adjust.png")],
        )

    def test_skips_adjust_when_auto_adjust_false(self):
        events = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            for entry in pic.tiles.values():
                entry.done = True

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
                options=PostprocessOptions(auto_adjust=False),
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

    def test_skips_when_applied_run_unchanged_and_desktop_ours(self):
        events = []
        state = {"last": None, "wallpaper_path": None}
        desktop = {"path": None}

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            events.append("compose")
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

        def set_wallpaper(path: Path):
            events.append("set")
            desktop["path"] = str(path.resolve())
            return True

        def get_desktop_wallpaper():
            return desktop["path"]

        with temporary_base_dir() as base_dir:
            kwargs = dict(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                get_desktop_wallpaper=get_desktop_wallpaper,
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
        self.assertIsNotNone(state.get("wallpaper_path"))

    def test_skips_when_state_preloaded_and_desktop_matches(self):
        events = []

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append("set")
            return True

        with temporary_base_dir() as base_dir:
            wall = Path(base_dir) / "wall.png"
            wall.write_bytes(b"img")
            state = {
                "last": ("2021-06-03 05:20:00", "4d", False, 0.0, 5.0, False, False),
                "wallpaper_path": str(wall.resolve()),
            }

            def get_desktop_wallpaper():
                return str(wall.resolve())

            skipped = run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                get_desktop_wallpaper=get_desktop_wallpaper,
                options=PostprocessOptions(auto_adjust=False, margin_top_percent=0.0, margin_bottom_percent=5.0),
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )

        self.assertEqual(events, ["fetch"])
        self.assertIsNone(skipped)

    def test_reapplies_when_fingerprint_same_but_desktop_changed(self):
        events = []
        state = {"last": None, "wallpaper_path": None}

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            events.append("compose")
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

        def set_wallpaper(path: Path):
            events.append(("set", path.name))
            return True

        def get_desktop_wallpaper():
            return r"C:\other\wallpaper.bmp"

        with temporary_base_dir() as base_dir:
            kwargs = dict(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                get_desktop_wallpaper=get_desktop_wallpaper,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            run_wallpaper_pipeline(**kwargs)
            first_name = events[-1][1]
            run_wallpaper_pipeline(**kwargs)

        self.assertEqual(
            events,
            [
                "fetch",
                "download",
                "compose",
                ("set", first_name),
                "fetch",
                ("set", first_name),
            ],
        )

    def test_full_rerun_when_fingerprint_same_but_wallpaper_file_missing(self):
        events = []
        state = {"last": None, "wallpaper_path": None}
        desktop = {"path": None}

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            events.append("compose")
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

        def set_wallpaper(path: Path):
            events.append("set")
            desktop["path"] = str(path.resolve())
            return True

        def get_desktop_wallpaper():
            return desktop["path"]

        with temporary_base_dir() as base_dir:
            kwargs = dict(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                get_desktop_wallpaper=get_desktop_wallpaper,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            run_wallpaper_pipeline(**kwargs)
            missing = Path(state["wallpaper_path"])
            missing.unlink()
            run_wallpaper_pipeline(**kwargs)

        self.assertEqual(
            events,
            [
                "fetch",
                "download",
                "compose",
                "set",
                "fetch",
                "download",
                "compose",
                "set",
            ],
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
            for entry in pic.tiles.values():
                entry.done = True

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

    def test_use_yesterday_local_time_skips_latest_fetch(self):
        events = []
        state = {"last": None, "wallpaper_path": None}

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2026-09-03 10:50:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append(("download", pic.year + pic.month + pic.day, pic.hour + pic.minute))
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append(("set", path.name))
            return True

        with (
            temporary_base_dir() as base_dir,
            patch(
                "src.wallpaper.pipeline.observation_time_yesterday_local",
                return_value=time.strptime("2026-09-02 09:20:00", "%Y-%m-%d %H:%M:%S"),
            ),
        ):
            result = run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                cleanup_after_apply=False,
                use_yesterday_local_time=True,
                applied_run_state=state,
                base_dir=base_dir,
            )

        self.assertEqual(result, "2026-09-02 09:20:00")
        self.assertEqual(
            events,
            [
                ("download", "20260902", "0920"),
                "compose",
                ("set", "4d20260902092000.png"),
            ],
        )
        self.assertEqual(state["last"][0], "2026-09-02 09:20:00")

    def test_skips_when_latest_observation_older_than_applied(self):
        events = []

        def fetch_observation_time():
            events.append("fetch")
            return time.strptime("2026-09-04 01:10:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            events.append("download")

        def compose_equal(pic):
            events.append("compose")

        def set_wallpaper(path: Path):
            events.append("set")
            return True

        with temporary_base_dir() as base_dir:
            wall = Path(base_dir) / "wall.png"
            wall.write_bytes(b"img")
            state = {
                "last": ("2026-09-04 01:40:00", "4d", False, 0.0, 5.0, False, False),
                "wallpaper_path": str(wall.resolve()),
            }

            result = run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                options=PostprocessOptions(auto_adjust=False, margin_top_percent=0.0, margin_bottom_percent=5.0),
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )

        self.assertIsNone(result)
        self.assertEqual(events, ["fetch"])
        self.assertEqual(state["last"][0], "2026-09-04 01:40:00")

    def test_reduce_banding_toggle_skips_download(self):
        downloads = []
        fetches = []

        def fetch_observation_time():
            fetches.append(1)
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(1)
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def set_wallpaper(path: Path):
            return True

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                options=PostprocessOptions(reduce_banding=False),
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            self.assertEqual(downloads, [1])
            self.assertEqual(fetches, [1])
            self.assertFalse(state["last"][5])
            wall = Path(state["wallpaper_path"])
            base = Path(state["wallpaper_base_path"])
            self.assertTrue(base.is_file())
            base_bytes = base.read_bytes()

            run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                options=PostprocessOptions(reduce_banding=True),
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            self.assertTrue(state["last"][5])
            self.assertEqual(downloads, [1])
            self.assertEqual(fetches, [1], "banding toggle must not fetch latest.json")
            self.assertNotEqual(wall.read_bytes(), base_bytes)

            run_wallpaper_pipeline(
                resolution_grade="4d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                options=PostprocessOptions(reduce_banding=False),
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )

            self.assertFalse(state["last"][5])
            self.assertEqual(downloads, [1])
            self.assertEqual(fetches, [1])
            self.assertEqual(wall.read_bytes(), base_bytes)

    def test_margin_toggle_skips_download_when_disk_present(self):
        downloads = []
        fetches = []
        set_names = []

        def fetch_observation_time():
            fetches.append(1)
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(1)
            for entry in pic.tiles.values():
                entry.done = True

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def set_wallpaper(path: Path):
            set_names.append(path.name)
            return True

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            with patch(
                "src.compose.equal.get_primary_screen_size",
                return_value=(200, 100),
            ):
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    options=PostprocessOptions(auto_adjust=True, margin_top_percent=0.0, margin_bottom_percent=5.0),
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                self.assertEqual(downloads, [1])
                self.assertEqual(fetches, [1])
                self.assertTrue(state["last"][2])
                disk = Path(state["wallpaper_disk_path"])
                self.assertTrue(disk.is_file())
                first_wall = Path(state["wallpaper_path"])
                self.assertTrue(first_wall.name.endswith("_adjust.png"))

                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    options=PostprocessOptions(auto_adjust=True, margin_top_percent=0.0, margin_bottom_percent=10.0),
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

                self.assertEqual(downloads, [1])
                self.assertEqual(fetches, [1], "margin toggle must not fetch latest.json")
                self.assertEqual(state["last"][4], 10.0)
                self.assertTrue(Path(state["wallpaper_path"]).is_file())
                self.assertGreaterEqual(len(set_names), 2)

    def test_refresh_postprocess_after_download_drops_typhoon(self):
        """下载中途关掉台风：上墙前 refresh 后新图不应再画台风。"""
        draws = []
        set_paths = []

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
            set_paths.append(Path(path).name)
            return True

        def fetch_center(_obs):
            return (29.024, 128.437)

        def fake_draw(image_path, xy, **kwargs):
            draws.append(kwargs.get("label"))
            return True

        from src.wallpaper.fingerprint import LivePostprocess

        live = {"show_typhoon_marker": True, "show_my_location": False}

        def refresh():
            live["show_typhoon_marker"] = False
            return LivePostprocess(
                options=PostprocessOptions(
                    auto_adjust=False,
                    margin_top_percent=0.0,
                    margin_bottom_percent=5.0,
                    reduce_banding=False,
                    show_typhoon_marker=live["show_typhoon_marker"],
                    show_my_location=False,
                ),
                cleanup_after_apply=False,
            )

        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.markers.draw_typhoon_marker", side_effect=fake_draw):
                result = run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    options=PostprocessOptions(show_typhoon_marker=True),
                    refresh_postprocess=refresh,
                    cleanup_after_apply=False,
                    applied_run_state={"last": None, "wallpaper_path": None},
                    base_dir=base_dir,
                )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertEqual(draws, [], "typhoon must not be drawn after refresh turns it off")
        self.assertEqual(len(set_paths), 1)


class WallpaperWritablePathTests(unittest.TestCase):
    def test_alternate_and_pick_writable(self):
        from src.wallpaper.paths import (
            alternate_wallpaper_path,
            pick_writable_wallpaper_path,
        )

        path = Path(r"E:\app\img\wall_adjust.png")
        alt = alternate_wallpaper_path(path)
        self.assertEqual(alt.name, "wall_adjust_b.png")
        self.assertEqual(alternate_wallpaper_path(alt), path)

        same = pick_writable_wallpaper_path(path, current_desktop=str(path))
        self.assertEqual(same, alt)
        free = pick_writable_wallpaper_path(path, current_desktop=r"E:\other\desk.png")
        self.assertEqual(free, path)

    def test_copy2_wallpaper_falls_back_on_winerror_1224(self):
        import shutil
        from unittest.mock import patch

        from src.wallpaper.paths import copy2_wallpaper

        real_copy2 = shutil.copy2
        with temporary_base_dir() as base_dir:
            src = base_dir / "src.png"
            dest = base_dir / "dest.png"
            Image.new("RGB", (8, 8), (1, 2, 3)).save(src)
            calls = {"n": 0}

            def fake_copy2(a, b):
                calls["n"] += 1
                if calls["n"] == 1:
                    err = OSError(22, "mapped")
                    err.winerror = 1224
                    raise err
                return real_copy2(a, b)

            with patch("src.wallpaper.paths.shutil.copy2", side_effect=fake_copy2):
                written = copy2_wallpaper(src, dest)

            self.assertEqual(written.name, "dest_b.png")
            self.assertTrue(written.is_file())


if __name__ == "__main__":
    unittest.main()
