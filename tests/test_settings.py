"""settings.json load/save/sanitize and resolve merge."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cli.args import Config
from src.settings import (
    applied_run_state_from_settings,
    default_settings,
    load_settings,
    persist_applied_run_state,
    resolve_runtime_settings,
    sanitize_settings,
    save_settings,
)


class SanitizeSettingsTests(unittest.TestCase):
    def test_keeps_valid_fields(self):
        cleaned = sanitize_settings(
            {
                "resolution": 4400,
                "auto_adjust": False,
                "margin_top_percent": 8.0,
                "margin_bottom_percent": 12.0,
                "cleanup_after_apply": False,
                "use_yesterday_local_time": True,
                "logging_enabled": True,
            }
        )
        self.assertEqual(cleaned["resolution"], 4400)
        self.assertFalse(cleaned["auto_adjust"])
        self.assertEqual(cleaned["margin_top_percent"], 8.0)
        self.assertEqual(cleaned["margin_bottom_percent"], 12.0)
        self.assertFalse(cleaned["cleanup_after_apply"])
        self.assertTrue(cleaned["use_yesterday_local_time"])
        self.assertTrue(cleaned["logging_enabled"])

    def test_skips_invalid_fields(self):
        cleaned = sanitize_settings(
            {
                "resolution": 999,
                "auto_adjust": "yes",
                "margin_top_percent": -1,
                "margin_bottom_percent": 101,
                "cleanup_after_apply": 1,
                "use_yesterday_local_time": "yes",
                "logging_enabled": "on",
                "extra": True,
            }
        )
        self.assertEqual(cleaned, {})

    def test_non_dict_returns_empty(self):
        self.assertEqual(sanitize_settings([1, 2]), {})


class SettingsFileIoTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = {
                "resolution": 4400,
                "auto_adjust": False,
                "margin_top_percent": 10.0,
                "margin_bottom_percent": 12.0,
                "cleanup_after_apply": False,
                "use_yesterday_local_time": True,
                "logging_enabled": True,
            }
            self.assertTrue(save_settings(data, path=path))
            loaded = load_settings(path)
            self.assertEqual(loaded["resolution"], 4400)
            self.assertFalse(loaded["auto_adjust"])
            self.assertEqual(loaded["margin_top_percent"], 10.0)
            self.assertEqual(loaded["margin_bottom_percent"], 12.0)
            self.assertFalse(loaded["cleanup_after_apply"])
            self.assertTrue(loaded["use_yesterday_local_time"])
            self.assertTrue(loaded["logging_enabled"])

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            self.assertEqual(load_settings(path), {})

    def test_bad_json_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{not-json", encoding="utf-8")
            self.assertEqual(load_settings(path), {})

    def test_save_fills_defaults_for_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            self.assertTrue(save_settings({"resolution": 1100}, path=path))
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["resolution"], 1100)
            self.assertEqual(raw["auto_adjust"], default_settings()["auto_adjust"])
            self.assertFalse(raw["logging_enabled"])
            self.assertFalse(raw["use_yesterday_local_time"])
            self.assertFalse(raw["reduce_banding"])
            self.assertFalse(raw["startup_enabled"])

    def test_partial_save_preserves_logging_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            self.assertTrue(save_settings({"logging_enabled": True}, path=path))
            self.assertTrue(save_settings({"resolution": 4400}, path=path))
            loaded = load_settings(path)
            self.assertEqual(loaded["resolution"], 4400)
            self.assertTrue(loaded["logging_enabled"])

    def test_persists_and_loads_applied_run_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            self.assertTrue(
                save_settings(
                    {
                        "last_run_key": [
                            "2026-09-03 02:10:00",
                            "20d",
                            True,
                            0.0,
                            5.0,
                        ],
                        "last_wallpaper_path": r"E:\app\img\wall.png",
                    },
                    path=path,
                )
            )
            loaded = load_settings(path)
            self.assertEqual(
                loaded["last_run_key"],
                ["2026-09-03 02:10:00", "20d", True, 0.0, 5.0, False],
            )
            self.assertEqual(loaded["last_wallpaper_path"], r"E:\app\img\wall.png")
            state = applied_run_state_from_settings(loaded)
            self.assertEqual(
                state["last"],
                ("2026-09-03 02:10:00", "20d", True, 0.0, 5.0, False),
            )
            self.assertEqual(state["wallpaper_path"], r"E:\app\img\wall.png")

            state["wallpaper_path"] = r"E:\app\img\wall2.png"
            self.assertTrue(persist_applied_run_state(state, path=path))
            loaded_again = load_settings(path)
            self.assertEqual(loaded_again["last_wallpaper_path"], r"E:\app\img\wall2.png")
            self.assertEqual(loaded_again["resolution"], default_settings()["resolution"])


class ResolveRuntimeSettingsTests(unittest.TestCase):
    def test_file_overrides_defaults(self):
        resolved = resolve_runtime_settings(
            {
                "resolution": None,
                "auto_adjust": None,
                "margin_top_percent": None,
                "margin_bottom_percent": None,
                "cleanup_after_apply": None,
                "use_yesterday_local_time": None,
            },
            file_settings={
                "resolution": 8800,
                "auto_adjust": False,
                "margin_top_percent": 8.0,
                "margin_bottom_percent": 10.0,
                "cleanup_after_apply": False,
                "use_yesterday_local_time": True,
            },
        )
        self.assertEqual(resolved["resolution"], 8800)
        self.assertFalse(resolved["auto_adjust"])
        self.assertEqual(resolved["margin_top_percent"], 8.0)
        self.assertEqual(resolved["margin_bottom_percent"], 10.0)
        self.assertFalse(resolved["cleanup_after_apply"])
        self.assertTrue(resolved["use_yesterday_local_time"])
        self.assertFalse(resolved["reduce_banding"])

    def test_cli_overrides_file(self):
        resolved = resolve_runtime_settings(
            {
                "resolution": 550,
                "auto_adjust": True,
                "margin_top_percent": 3.0,
                "margin_bottom_percent": None,
                "cleanup_after_apply": None,
                "use_yesterday_local_time": False,
            },
            file_settings={
                "resolution": 8800,
                "auto_adjust": False,
                "margin_top_percent": 8.0,
                "margin_bottom_percent": 12.0,
                "cleanup_after_apply": False,
                "use_yesterday_local_time": True,
            },
        )
        self.assertEqual(resolved["resolution"], 550)
        self.assertTrue(resolved["auto_adjust"])
        self.assertEqual(resolved["margin_top_percent"], 3.0)
        self.assertEqual(resolved["margin_bottom_percent"], 12.0)
        self.assertFalse(resolved["cleanup_after_apply"])
        self.assertFalse(resolved["use_yesterday_local_time"])

    def test_absent_cli_keeps_file(self):
        resolved = resolve_runtime_settings(
            {
                "resolution": None,
                "auto_adjust": None,
                "margin_top_percent": None,
                "margin_bottom_percent": None,
                "cleanup_after_apply": None,
                "use_yesterday_local_time": None,
                "logging_enabled": None,
            },
            file_settings={"resolution": 4400},
        )
        self.assertEqual(resolved["resolution"], 4400)
        self.assertEqual(resolved["auto_adjust"], default_settings()["auto_adjust"])
        self.assertFalse(resolved["logging_enabled"])
        self.assertFalse(resolved["use_yesterday_local_time"])

    def test_default_logging_disabled(self):
        resolved = resolve_runtime_settings(
            {
                "resolution": None,
                "auto_adjust": None,
                "margin_top_percent": None,
                "margin_bottom_percent": None,
                "cleanup_after_apply": None,
                "use_yesterday_local_time": None,
                "logging_enabled": None,
            },
            file_settings={},
        )
        self.assertFalse(resolved["logging_enabled"])
        self.assertFalse(resolved["use_yesterday_local_time"])


def _config_with_file(argv, file_settings):
    Config._instance = None
    with (
        patch.object(sys, "argv", argv),
        patch(
            "src.cli.args.resolve_runtime_settings",
            side_effect=lambda cli_values, **kwargs: resolve_runtime_settings(
                cli_values,
                file_settings=file_settings,
            ),
        ),
    ):
        return Config()


class ConfigUsesSettingsFileTests(unittest.TestCase):
    def tearDown(self):
        Config._instance = None

    def test_config_reads_file_when_cli_omitted(self):
        config = _config_with_file(
            ["run.py"],
            {
                "resolution": 4400,
                "auto_adjust": False,
                "margin_top_percent": 8.0,
                "margin_bottom_percent": 10.0,
                "cleanup_after_apply": False,
            },
        )
        self.assertEqual(config.get_download_resolution(), 4400)
        self.assertFalse(config.is_auto_adjust_picture())
        self.assertEqual(config.get_margin_top_percent(), 8.0)
        self.assertFalse(config.is_cleanup_after_apply())
        self.assertFalse(config.is_use_yesterday_local_time())

    def test_cli_overrides_resolved_file(self):
        config = _config_with_file(
            ["run.py", "-r", "550", "--no-adjust", "--use-yesterday-local-time"],
            {
                "resolution": 4400,
                "auto_adjust": True,
                "margin_top_percent": 8.0,
                "margin_bottom_percent": 10.0,
                "cleanup_after_apply": True,
                "use_yesterday_local_time": False,
            },
        )
        self.assertEqual(config.get_download_resolution(), 550)
        self.assertFalse(config.is_auto_adjust_picture())
        self.assertEqual(config.get_margin_top_percent(), 8.0)
        self.assertTrue(config.is_use_yesterday_local_time())


if __name__ == "__main__":
    unittest.main()
