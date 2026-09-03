"""Seam: cleanup_after_wallpaper_apply keeps wallpaper file and drops tiles/old runs."""

import time
import unittest
from pathlib import Path

from src.cleanup import cleanup_after_wallpaper_apply
from src.wallpaper.pipeline import run_wallpaper_pipeline
from tests.workdir_paths import temporary_base_dir


class CleanupAfterApplyTests(unittest.TestCase):
    def test_keeps_wallpaper_deletes_tiles_extras_and_old_runs(self):
        with temporary_base_dir() as tmp:
            img_root = tmp / "img"
            current = img_root / "20210603052000"
            old = img_root / "20210603051000"
            tiles = current / "4d" / "0"
            complete = current / "complete"
            tiles.mkdir(parents=True)
            complete.mkdir(parents=True)
            (old / "complete").mkdir(parents=True)

            tile = tiles / "tile.png"
            equal = complete / "4d20210603052000.png"
            keep = complete / "4d20210603052000_adjust.png"
            old_file = old / "complete" / "old.png"
            for path in (tile, equal, keep, old_file):
                path.write_bytes(b"x")

            cleanup_after_wallpaper_apply(
                img_root=img_root,
                current_run_root=current,
                keep_file=keep,
            )

            self.assertTrue(keep.is_file())
            self.assertFalse(tile.exists())
            self.assertFalse((current / "4d").exists())
            self.assertFalse(equal.exists())
            self.assertFalse(old.exists())
            self.assertTrue(complete.is_dir())

    def test_pipeline_cleans_when_enabled(self):
        with temporary_base_dir() as base:
            img_root = base / "img"
            keep_name = "4d20210603052000_adjust.png"

            def fetch_observation_time():
                return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

            def download_tiles(pic):
                for entry in pic.dic.values():
                    entry[1] = 1
                run_root = Path(pic.folder_path).parent
                tile_dir = run_root / pic.str_equal / "0"
                tile_dir.mkdir(parents=True, exist_ok=True)
                (tile_dir / "tile.png").write_bytes(b"t")
                Path(pic.folder_path).mkdir(parents=True, exist_ok=True)
                Path(pic.final_path_equal).write_bytes(b"e")

            def compose_equal(pic):
                Path(pic.final_path_equal).write_bytes(b"e")

            def adjust_wallpaper(pic):
                out = Path(pic.final_path_equal).with_name(keep_name)
                out.write_bytes(b"a")
                return out

            def set_wallpaper(path: Path):
                self.assertTrue(path.is_file())
                return True

            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                adjust_wallpaper=adjust_wallpaper,
                set_wallpaper=set_wallpaper,
                auto_adjust=True,
                cleanup_after_apply=True,
                base_dir=base,
            )

            keep = img_root / "20210603052000" / "complete" / keep_name
            self.assertTrue(keep.is_file())
            self.assertFalse((img_root / "20210603052000" / "4d").exists())
            self.assertFalse(
                (
                    img_root / "20210603052000" / "complete" / "4d20210603052000.png"
                ).exists()
            )

    def test_pipeline_skips_cleanup_when_set_wallpaper_fails(self):
        with temporary_base_dir() as base:

            def fetch_observation_time():
                return time.strptime("2021-06-03 05:20:00", "%Y-%m-%d %H:%M:%S")

            def download_tiles(pic):
                for entry in pic.dic.values():
                    entry[1] = 1
                Path(pic.folder_path).mkdir(parents=True, exist_ok=True)
                tile_dir = Path(pic.folder_path).parent / pic.str_equal / "0"
                tile_dir.mkdir(parents=True, exist_ok=True)
                (tile_dir / "tile.png").write_bytes(b"t")
                Path(pic.final_path_equal).write_bytes(b"e")

            def compose_equal(pic):
                Path(pic.final_path_equal).write_bytes(b"e")

            def set_wallpaper(path: Path):
                return False

            run_wallpaper_pipeline(
                fetch_observation_time=fetch_observation_time,
                download_tiles=download_tiles,
                compose_equal=compose_equal,
                set_wallpaper=set_wallpaper,
                auto_adjust=False,
                cleanup_after_apply=True,
                base_dir=base,
            )

            tile = base / "img" / "20210603052000" / "4d" / "0" / "tile.png"
            self.assertTrue(tile.is_file())


if __name__ == "__main__":
    unittest.main()
