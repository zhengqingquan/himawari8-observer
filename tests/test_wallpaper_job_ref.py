"""Seam: WallpaperJobRef is shared and can replace frozen grade at runtime."""

import unittest

from src.wallpaper.job import WallpaperJobRef


class WallpaperJobRefTests(unittest.TestCase):
    def test_call_uses_current_grade(self):
        grades = []

        def fake_build(resolution_grade, *, auto_adjust=False, **_kwargs):
            def job():
                grades.append((resolution_grade, auto_adjust))

            return job

        ref = WallpaperJobRef("4d", auto_adjust=True, build_job=fake_build, persist_state=False)
        ref()
        ref.set_resolution_grade("8d")
        ref()
        self.assertEqual(grades, [("4d", True), ("8d", True)])

    def test_set_pixel_side_maps_to_grade(self):
        grades = []

        def fake_build(resolution_grade, *, auto_adjust=False, **_kwargs):
            def job():
                grades.append(resolution_grade)

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build, persist_state=False)
        ref.set_pixel_side(8800)
        self.assertEqual(ref.resolution_grade, "16d")
        self.assertEqual(ref.pixel_side, 8800)
        ref()
        self.assertEqual(grades, ["16d"])

    def test_set_margin_rebuilds_job(self):
        builds = []

        def fake_build(
            resolution_grade,
            *,
            auto_adjust=False,
            margin_top_percent=5.0,
            margin_bottom_percent=5.0,
            **_kwargs,
        ):
            builds.append(
                (resolution_grade, auto_adjust, margin_top_percent, margin_bottom_percent)
            )

            def job():
                return None

            return job

        ref = WallpaperJobRef(
            "4d",
            margin_top_percent=5.0,
            margin_bottom_percent=5.0,
            build_job=fake_build,
            persist_state=False,
        )
        ref.set_margin_bottom_percent(12.0)
        ref.set_auto_adjust(False)
        self.assertEqual(ref.margin_bottom_percent, 12.0)
        self.assertFalse(ref.auto_adjust)
        self.assertEqual(
            builds,
            [
                ("4d", False, 5.0, 5.0),
                ("4d", False, 5.0, 12.0),
                ("4d", False, 5.0, 12.0),
            ],
        )

    def test_set_cleanup_after_apply_rebuilds_job(self):
        flags = []

        def fake_build(resolution_grade, *, cleanup_after_apply=True, **_kwargs):
            flags.append(cleanup_after_apply)

            def job():
                return None

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build, persist_state=False)
        self.assertTrue(ref.cleanup_after_apply)
        ref.set_cleanup_after_apply(False)
        self.assertFalse(ref.cleanup_after_apply)
        self.assertEqual(flags, [True, False])

    def test_set_use_yesterday_local_time_rebuilds_job(self):
        flags = []

        def fake_build(resolution_grade, *, use_yesterday_local_time=False, **_kwargs):
            flags.append(use_yesterday_local_time)

            def job():
                return None

            return job

        ref = WallpaperJobRef("4d", build_job=fake_build, persist_state=False)
        self.assertFalse(ref.use_yesterday_local_time)
        ref.set_use_yesterday_local_time(True)
        self.assertTrue(ref.use_yesterday_local_time)
        self.assertEqual(flags, [False, True])

    def test_applied_observation_time_from_run_state_and_survives_rebuild(self):
        ref = WallpaperJobRef("4d", build_job=_noop_build, persist_state=False)
        self.assertIsNone(ref.applied_observation_time)

        ref._applied_run_state["last"] = (
            "2026-09-03 02:10:00",
            "4d",
            False,
            0.0,
            5.0,
        )
        self.assertEqual(ref.applied_observation_time, "2026-09-03 02:10:00")

        ref.set_resolution_grade("8d")
        self.assertIsNone(ref._applied_run_state.get("last"))
        self.assertEqual(ref.applied_observation_time, "2026-09-03 02:10:00")

    def test_init_hydrates_observation_time_from_applied_state(self):
        state = {
            "last": ("2026-09-03 02:10:00", "4d", True, 0.0, 5.0),
            "wallpaper_path": r"E:\app\img\wall.png",
        }
        ref = WallpaperJobRef(
            "4d",
            auto_adjust=True,
            margin_top_percent=0.0,
            margin_bottom_percent=5.0,
            build_job=_noop_build,
            applied_run_state=state,
            persist_state=False,
        )
        self.assertEqual(ref.applied_observation_time, "2026-09-03 02:10:00")
        self.assertEqual(ref._applied_run_state["wallpaper_path"], r"E:\app\img\wall.png")

    def test_on_applied_called_after_call(self):
        calls = []

        ref = WallpaperJobRef("4d", build_job=_noop_build, persist_state=False)
        ref.set_on_applied(lambda: calls.append(1))
        ref()
        self.assertEqual(calls, [1])

    def test_on_applied_exception_does_not_raise(self):
        def boom():
            raise RuntimeError("title refresh failed")

        ref = WallpaperJobRef("4d", build_job=_noop_build, persist_state=False)
        ref.set_on_applied(boom)
        ref()  # must not raise


class WallpaperJobRefProgressiveTests(unittest.TestCase):
    def test_progressive_runs_preview_then_target(self):
        grades = []
        states = []
        flags = []

        def fake_pipeline(
            *,
            resolution_grade=None,
            applied_run_state=None,
            cleanup_after_apply=True,
            record_run_key=True,
            **_kwargs,
        ):
            grades.append(resolution_grade)
            states.append(applied_run_state)
            flags.append(
                {
                    "cleanup_after_apply": cleanup_after_apply,
                    "record_run_key": record_run_key,
                }
            )

        ref = WallpaperJobRef(
            "20d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        ref.run_progressive()
        self.assertEqual(grades, ["4d", "20d"])
        self.assertIs(states[0], states[1])
        self.assertFalse(flags[0]["cleanup_after_apply"])
        self.assertFalse(flags[0]["record_run_key"])
        self.assertTrue(flags[1]["cleanup_after_apply"])
        self.assertTrue(flags[1]["record_run_key"])

    def test_progressive_skips_preview_when_target_not_higher(self):
        grades = []

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)

        ref = WallpaperJobRef(
            "4d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        ref.run_progressive()
        self.assertEqual(grades, ["4d"])

        grades.clear()
        ref.set_resolution_grade("2d")
        ref.run_progressive()
        self.assertEqual(grades, ["2d"])

    def test_progressive_continues_after_preview_raises(self):
        grades = []

        def fake_pipeline(*, resolution_grade=None, **_kwargs):
            grades.append(resolution_grade)
            if resolution_grade == "4d":
                raise RuntimeError("preview failed")

        ref = WallpaperJobRef(
            "20d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        ref.run_progressive()
        self.assertEqual(grades, ["4d", "20d"])

    def test_on_applied_called_after_progressive(self):
        calls = []

        def fake_pipeline(**_kwargs):
            return None

        ref = WallpaperJobRef(
            "20d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        ref.set_on_applied(lambda: calls.append(1))
        ref.run_progressive()
        self.assertEqual(calls, [1])

    def test_progressive_preview_refreshes_display_time_without_fingerprint(self):
        obs = "2026-09-03 02:10:00"
        notifies = []

        def fake_pipeline(
            *,
            resolution_grade=None,
            applied_run_state=None,
            record_run_key=True,
            **_kwargs,
        ):
            if applied_run_state is not None:
                applied_run_state["applied_grade"] = resolution_grade
                if record_run_key:
                    applied_run_state["last"] = (obs, resolution_grade, False, 0.0, 5.0)
            return obs

        ref = WallpaperJobRef(
            "20d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        ref.set_on_applied(
            lambda: notifies.append((ref.applied_observation_time, ref.applied_resolution_grade))
        )
        ref.run_progressive()

        self.assertEqual(notifies, [(obs, "4d"), (obs, "20d")])
        self.assertEqual(ref.applied_observation_time, obs)
        self.assertEqual(ref.applied_resolution_grade, "20d")
        self.assertEqual(ref.applied_pixel_side, 11000)
        self.assertEqual(ref._applied_run_state["last"][0], obs)

    def test_progressive_preview_notify_before_target_without_writing_last(self):
        obs = "2026-09-03 02:10:00"
        mid_last = []
        mid_time = []
        mid_grade = []

        def fake_pipeline(
            *,
            resolution_grade=None,
            applied_run_state=None,
            record_run_key=True,
            **_kwargs,
        ):
            if resolution_grade == "4d":
                if applied_run_state is not None:
                    applied_run_state["applied_grade"] = resolution_grade
                return obs
            mid_last.append(applied_run_state.get("last") if applied_run_state else None)
            mid_time.append(ref.applied_observation_time)
            mid_grade.append(ref.applied_resolution_grade)
            if applied_run_state is not None:
                applied_run_state["applied_grade"] = resolution_grade
                if record_run_key:
                    applied_run_state["last"] = (obs, resolution_grade, False, 0.0, 5.0)
            return obs

        ref = WallpaperJobRef(
            "20d",
            run_pipeline=fake_pipeline,
            build_job=_noop_build,
            persist_state=False,
        )
        notifies = []
        ref.set_on_applied(lambda: notifies.append(ref.applied_observation_time))
        ref.run_progressive()

        self.assertEqual(notifies[0], obs)
        self.assertIsNone(mid_last[0])
        self.assertEqual(mid_time[0], obs)
        self.assertEqual(mid_grade[0], "4d")


def _noop_build(resolution_grade, **_kwargs):
    def job():
        return None

    return job


if __name__ == "__main__":
    unittest.main()
