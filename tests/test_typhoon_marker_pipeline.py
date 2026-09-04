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
            with patch("src.wallpaper.postprocess.draw_typhoon_marker", side_effect=fake_draw):
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

    def test_typhoon_only_toggle_on_skips_download(self):
        downloads = []
        draws = []
        fetches = []
        center_fetches = []

        def fetch_observation_time():
            fetches.append(1)
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(1)
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
            center_fetches.append(1)
            return (29.024, 128.437)

        def fake_draw(image_path, xy, **kwargs):
            draws.append(xy)
            return True

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.postprocess.draw_typhoon_marker", side_effect=fake_draw):
                # 全量开台风：拉中心并写入缓存
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                self.assertEqual(downloads, [1])
                self.assertEqual(fetches, [1])
                self.assertEqual(center_fetches, [1])
                self.assertEqual(len(draws), 1)
                self.assertTrue(state["last"][6])
                self.assertEqual(
                    state["typhoon_center_cache"]["observation_time"],
                    "2021-06-03 05:20:00",
                )

                # 关掉（复原底图）
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=False,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                self.assertFalse(state["last"][6])

                # 再开：只用缓存，不请求网络
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(downloads, [1])
        self.assertEqual(fetches, [1], "typhoon toggle must not fetch latest.json")
        self.assertEqual(center_fetches, [1], "typhoon toggle must use cache only")
        self.assertEqual(len(draws), 2)
        self.assertTrue(state["last"][6])

    def test_typhoon_toggle_on_without_matching_cache_skips_marker(self):
        draws = []
        center_fetches = []

        def set_wallpaper(path: Path):
            return True

        def fetch_center(_obs):
            center_fetches.append(1)
            return (29.024, 128.437)

        def fake_draw(image_path, xy, **kwargs):
            draws.append(xy)
            return True

        with temporary_base_dir() as base_dir:
            complete = Path(base_dir) / "img" / "20210603052000" / "complete"
            complete.mkdir(parents=True)
            wall = complete / "4d20210603052000.png"
            base = complete / "4d20210603052000_base.png"
            Image.new("RGB", (64, 64), (1, 2, 3)).save(wall)
            Image.new("RGB", (64, 64), (1, 2, 3)).save(base)
            state = {
                "last": ("2021-06-03 05:20:00", "4d", False, 0.0, 5.0, False, False),
                "wallpaper_path": str(wall),
                "wallpaper_base_path": str(base),
                # 缓存是别的观测时间 → 不得画
                "typhoon_center_cache": {
                    "observation_time": "2021-06-03 05:10:00",
                    "lat": 29.024,
                    "lon": 128.437,
                },
            }
            with patch("src.wallpaper.postprocess.draw_typhoon_marker", side_effect=fake_draw):
                result = run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=lambda: (_ for _ in ()).throw(
                        RuntimeError("must not fetch latest")
                    ),
                    download_tiles=lambda pic: None,
                    compose_equal=lambda pic: None,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertEqual(draws, [])
        self.assertEqual(center_fetches, [])
        self.assertTrue(state["last"][6])

    def test_typhoon_only_toggle_off_restores_base_without_download(self):
        downloads = []
        fetches = []
        set_paths = []

        def fetch_observation_time():
            fetches.append(1)
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(1)
            for entry in pic.tiles.values():
                entry[1] = 1

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (pic.pic_side, pic.pic_side), (10, 20, 30)).save(
                pic.final_path_equal
            )

        def set_wallpaper(path: Path):
            set_paths.append(path.name)
            return True

        def fetch_center(_obs):
            return (29.024, 128.437)

        state = {"last": None, "wallpaper_path": None}
        with temporary_base_dir() as base_dir:
            with patch("src.wallpaper.postprocess.draw_typhoon_marker", return_value=True):
                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )
                wall = Path(state["wallpaper_path"])
                base = Path(state["wallpaper_base_path"])
                self.assertTrue(base.is_file())
                self.assertTrue(state["last"][6])
                self.assertEqual(fetches, [1])

                run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=download_tiles,
                    compose_equal=compose_equal,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=fetch_center,
                    show_typhoon_marker=False,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(downloads, [1])
        self.assertEqual(fetches, [1], "typhoon toggle must not fetch latest.json")
        self.assertFalse(state["last"][6])
        self.assertEqual(set_paths[-1], wall.name)

    def test_typhoon_toggle_skips_latest_even_if_fetch_would_fail(self):
        """回归：开关不得先拉 latest；有匹配缓存时从缓存画点。"""

        def fetch_observation_time():
            raise RuntimeError("latest.json must not be fetched on typhoon toggle")

        def set_wallpaper(path: Path):
            return True

        with temporary_base_dir() as base_dir:
            complete = Path(base_dir) / "img" / "20210603052000" / "complete"
            complete.mkdir(parents=True)
            wall = complete / "4d20210603052000.png"
            base = complete / "4d20210603052000_base.png"
            Image.new("RGB", (64, 64), (1, 2, 3)).save(wall)
            Image.new("RGB", (64, 64), (1, 2, 3)).save(base)
            state = {
                "last": ("2021-06-03 05:20:00", "4d", False, 0.0, 5.0, False, False),
                "wallpaper_path": str(wall),
                "wallpaper_base_path": str(base),
                "typhoon_center_cache": {
                    "observation_time": "2021-06-03 05:20:00",
                    "lat": 29.024,
                    "lon": 128.437,
                },
            }
            with patch("src.wallpaper.postprocess.draw_typhoon_marker", return_value=True) as draw:
                result = run_wallpaper_pipeline(
                    resolution_grade="4d",
                    fetch_observation_time=fetch_observation_time,
                    download_tiles=lambda pic: None,
                    compose_equal=lambda pic: None,
                    set_wallpaper=set_wallpaper,
                    fetch_typhoon_center_fn=lambda _obs: (_ for _ in ()).throw(
                        RuntimeError("must not fetch typhoon json")
                    ),
                    show_typhoon_marker=True,
                    cleanup_after_apply=False,
                    applied_run_state=state,
                    base_dir=base_dir,
                )

        self.assertEqual(result, "2021-06-03 05:20:00")
        self.assertTrue(state["last"][6])
        self.assertTrue(draw.called)

    def test_grade_change_still_downloads(self):
        downloads = []

        def fetch_observation_time():
            return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

        def download_tiles(pic):
            downloads.append(pic.grade)
            for entry in pic.tiles.values():
                entry[1] = 1

        def compose_equal(pic):
            Path(pic.final_path_equal).parent.mkdir(parents=True, exist_ok=True)
            Path(pic.final_path_equal).write_bytes(b"img")

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
                show_typhoon_marker=False,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )
            run_wallpaper_pipeline(
                resolution_grade="8d",
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                show_typhoon_marker=False,
                cleanup_after_apply=False,
                applied_run_state=state,
                base_dir=base_dir,
            )

        self.assertEqual(downloads, ["4d", "8d"])


if __name__ == "__main__":
    unittest.main()
