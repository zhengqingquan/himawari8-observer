"""托盘选择观测时间点：tkinter 小窗（本地日期+时间）。"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from datetime import datetime, timezone
from time import struct_time
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Callable

from src.download.observation import (
    OBS_TIME_FMT,
    floor_datetime_to_full_disk_utc,
    observation_time_from_local,
)
from src.settings import load_settings, save_settings
from src.tray.actions import format_observation_local_time, tray_icon_path
from src.wallpaper.update import pause, run_wallpaper_update

if TYPE_CHECKING:
    from src.wallpaper.job import WallpaperJobRef

_DATE_FMT = "%Y-%m-%d"
_TIME_FMT = "%H:%M"

_dialog_lock = threading.Lock()
_dialog_root: tk.Tk | None = None


def _load_dialog_position() -> dict[str, int] | None:
    pos = load_settings().get("time_pick_dialog_position")
    if isinstance(pos, dict) and "x" in pos and "y" in pos:
        return {"x": int(pos["x"]), "y": int(pos["y"])}
    return None


def _save_dialog_position(root: tk.Tk) -> None:
    try:
        root.update_idletasks()
        x = int(root.winfo_x())
        y = int(root.winfo_y())
    except tk.TclError:
        return
    save_settings({"time_pick_dialog_position": {"x": x, "y": y}})


def _default_local_fields(job_ref: WallpaperJobRef) -> tuple[str, str]:
    """默认日期/时间：优先当前壁纸对应本地时刻，否则本机现在；分钟向下取整到 10。"""
    obs = job_ref.applied_observation_time
    if obs:
        try:
            local_str = format_observation_local_time(obs)
            local_dt = datetime.strptime(local_str, OBS_TIME_FMT).astimezone()
        except (ValueError, OSError):
            local_dt = datetime.now().astimezone()
    else:
        local_dt = datetime.now().astimezone()
    floored_utc = floor_datetime_to_full_disk_utc(local_dt)
    local_slot = floored_utc.astimezone()
    return local_slot.strftime(_DATE_FMT), local_slot.strftime(_TIME_FMT)


def _parse_local_inputs(date_text: str, time_text: str) -> datetime | str:
    """解析本地日期+时间；失败返回错误文案。"""
    date_raw = date_text.strip()
    time_raw = time_text.strip()
    try:
        date_part = datetime.strptime(date_raw, _DATE_FMT).date()
    except ValueError:
        return "日期格式应为 YYYY-MM-DD"
    try:
        time_part = datetime.strptime(time_raw, _TIME_FMT).time()
    except ValueError:
        return "时间格式应为 HH:MM"
    naive = datetime.combine(date_part, time_part)
    local_dt = naive.astimezone()
    if local_dt > datetime.now().astimezone():
        return "不能选择未来时间"
    return local_dt


def _trigger_observation_update(job_ref: WallpaperJobRef, obs: struct_time) -> None:
    def _run() -> None:
        try:
            job_ref.set_observation_override(obs)
            run_wallpaper_update(job_ref, respect_pause=False, progressive=True)
        except Exception:
            logging.exception("Wallpaper update for selected observation failed")

    threading.Thread(
        target=_run,
        daemon=True,
        name="time-pick-wallpaper-update",
    ).start()


def open_time_pick_dialog(
    job_ref: WallpaperJobRef,
    *,
    on_applied: Callable[[], None] | None = None,
) -> None:
    """在守护线程打开选时点窗；确认后暂停定时更新并拉取该观测帧。"""

    def _run() -> None:
        global _dialog_root
        with _dialog_lock:
            existing = _dialog_root
            if existing is not None:
                try:
                    existing.after(0, existing.lift)
                    existing.after(0, existing.focus_force)
                    return
                except tk.TclError:
                    _dialog_root = None

            root = tk.Tk()
            _dialog_root = root

        root.title("选择壁纸时间点")
        root.resizable(False, False)
        icon_photo = None
        try:
            icon_photo = tk.PhotoImage(file=str(tray_icon_path()))
            root.iconphoto(True, icon_photo)
        except tk.TclError:
            logging.exception("Failed to set time-pick dialog icon")

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        default_date, default_time = _default_local_fields(job_ref)
        date_var = tk.StringVar(value=default_date)
        time_var = tk.StringVar(value=default_time)

        ttk.Label(frame, text="本地日期").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=date_var, width=14).grid(
            row=0, column=1, sticky="e", pady=2, padx=(8, 0)
        )
        ttk.Label(frame, text="本地时间").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame, textvariable=time_var, width=14).grid(
            row=1, column=1, sticky="e", pady=2, padx=(8, 0)
        )
        ttk.Label(frame, text="将对齐到 UTC 全盘 10 分钟观测档，并暂停定时更新。").grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )

        def _close_window() -> None:
            _save_dialog_position(root)
            try:
                root.quit()
            except tk.TclError:
                pass
            try:
                root.destroy()
            except tk.TclError:
                pass

        def _on_ok() -> None:
            parsed = _parse_local_inputs(date_var.get(), time_var.get())
            if isinstance(parsed, str):
                messagebox.showerror("无效时间", parsed, parent=root)
                return
            obs = observation_time_from_local(parsed)
            utc_text = datetime(*obs[:6], tzinfo=timezone.utc).strftime(OBS_TIME_FMT)
            pause()
            save_settings({"updates_paused": True})
            logging.info(
                "Time-pick wallpaper: local=%s %s -> utc=%s; updates paused",
                date_var.get().strip(),
                time_var.get().strip(),
                utc_text,
            )
            _trigger_observation_update(job_ref, obs)
            if on_applied is not None:
                on_applied()
            _close_window()

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(buttons, text="确认", command=_on_ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="取消", command=_close_window).pack(side=tk.LEFT, padx=4)

        root.protocol("WM_DELETE_WINDOW", _close_window)

        saved = _load_dialog_position()
        if saved is not None:
            root.geometry(f"+{saved['x']}+{saved['y']}")

        root.mainloop()

        with _dialog_lock:
            if _dialog_root is root:
                _dialog_root = None

    threading.Thread(target=_run, daemon=True, name="time-pick-dialog").start()
