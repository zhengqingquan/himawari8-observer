"""减轻色带参数：tkinter 小窗（零新依赖）。"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from src.compose.equal import DEFAULT_DEBAND, DebandParams
from src.settings import load_settings, parse_deband_form, save_settings
from src.tray.actions import persist_job_settings, tray_icon_path
from src.wallpaper.update import run_wallpaper_update

if TYPE_CHECKING:
    from src.wallpaper.job import WallpaperJobRef

# 键、标签、悬停说明（作用 + 取值范围，与 settings 校验一致）
_FIELD_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "blur_radius",
        "模糊半径",
        "高斯邻域均值的模糊半径，越大平坦区越平滑。\n取值范围：(0, 64]，默认 10.0",
    ),
    (
        "diff_scale",
        "差放大",
        "原图与均值差的放大系数；越大越只处理更平坦区域。\n取值范围：[1, 32] 整数，默认 5",
    ),
    (
        "noise_sigma",
        "噪点强度",
        "叠加微粒噪点强度，用于打散量化台阶。\n取值范围：[0, 64]，默认 2.0",
    ),
    (
        "black_luma_max",
        "近黑阈值",
        "亮度 ≤ 此值的近黑像素（太空/黑边）保持原样。\n取值范围：[0, 64] 整数，默认 2",
    ),
    (
        "terminator_mu_half",
        "晨昏带半宽 μ",
        "太阳点积 μ 半宽；|μ| 小于此值才算晨昏带。\n取值范围：(0, 1]，默认 0.20",
    ),
    (
        "terminator_mu_steps",
        "μ 采样层数",
        "沿 μ 方向采样的层数，影响晨昏带掩码厚度。\n取值范围：[2, 64] 整数，默认 15",
    ),
    (
        "terminator_samples",
        "圆环采样点数",
        "每层晨昏圆环的采样点数。\n取值范围：[36, 2880] 整数，默认 720",
    ),
    (
        "terminator_mask_side",
        "掩码分辨率",
        "晨昏带掩码先在此边长内计算，再放大到全盘。\n取值范围：[64, 2048] 整数，默认 512",
    ),
    (
        "terminator_mask_blur",
        "掩码模糊",
        "掩码边缘高斯模糊半径，做软过渡。\n取值范围：[0, 64]，默认 6.0",
    ),
    (
        "terminator_stamp_r",
        "采样点印章半径",
        "每个采样点写入的方块半径（像素），连成更粗的带。\n取值范围：[0, 16] 整数，默认 2",
    ),
)

_dialog_lock = threading.Lock()
_dialog_root: tk.Tk | None = None


class _HoverTip:
    """鼠标悬停提示（绑定到 Label / Entry）。"""

    def __init__(self, widget: tk.Widget, text: str, *, delay_ms: int = 450) -> None:
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        self._cancel_schedule()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _on_leave(self, _event: tk.Event | None = None) -> None:
        self._cancel_schedule()
        self._hide()

    def _cancel_schedule(self) -> None:
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip is not None:
            return
        try:
            x = self._widget.winfo_rootx() + 16
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        except tk.TclError:
            return
        tip = tk.Toplevel(self._widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        try:
            tip.attributes("-topmost", True)
        except tk.TclError:
            pass
        label = tk.Label(
            tip,
            text=self._text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=6,
            pady=4,
        )
        label.pack()
        self._tip = tip

    def _hide(self) -> None:
        tip = self._tip
        self._tip = None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass


def _load_dialog_position() -> dict[str, int] | None:
    pos = load_settings().get("deband_dialog_position")
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
    save_settings({"deband_dialog_position": {"x": x, "y": y}})


def _trigger_wallpaper_update(job_ref: WallpaperJobRef) -> None:
    if not job_ref.reduce_banding:
        return
    threading.Thread(
        target=run_wallpaper_update,
        args=(job_ref,),
        daemon=True,
        name="deband-params-update",
    ).start()


def open_deband_params_dialog(job_ref: WallpaperJobRef) -> None:
    """在守护线程打开色带参数窗；已开则置前。"""

    def _run() -> None:
        global _dialog_root
        with _dialog_lock:
            existing = _dialog_root
            if existing is not None:
                try:
                    # 投递到持有 Tk 的线程，避免跨线程直接操作窗口。
                    existing.after(0, existing.lift)
                    existing.after(0, existing.focus_force)
                    return
                except tk.TclError:
                    _dialog_root = None

            root = tk.Tk()
            _dialog_root = root

        root.title("减轻色带参数")
        root.resizable(False, False)
        # icon_photo 须活到 mainloop 结束，否则标题栏图标会被回收。
        icon_photo = None
        try:
            icon_photo = tk.PhotoImage(file=str(tray_icon_path()))
            root.iconphoto(True, icon_photo)
        except tk.TclError:
            logging.exception("Failed to set deband dialog icon")

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        entries: dict[str, tk.StringVar] = {}
        # 保持 tip 引用，避免被回收后悬停失效。
        tips: list[_HoverTip] = []
        current = job_ref.deband
        for row, (key, label, tip_text) in enumerate(_FIELD_ROWS):
            name_label = ttk.Label(frame, text=label)
            name_label.grid(row=row, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=str(getattr(current, key)))
            entries[key] = var
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=row, column=1, sticky="e", pady=2, padx=(8, 0))
            tips.append(_HoverTip(name_label, tip_text))
            tips.append(_HoverTip(entry, tip_text))

        def _fill(params: DebandParams) -> None:
            for key, _label, _tip in _FIELD_ROWS:
                entries[key].set(str(getattr(params, key)))

        def _close_window() -> None:
            _save_dialog_position(root)
            # 先 quit 结束 mainloop，再 destroy；勿在持锁路径里关窗。
            try:
                root.quit()
            except tk.TclError:
                pass
            try:
                root.destroy()
            except tk.TclError:
                pass

        def _apply_form() -> bool:
            """校验并落盘；成功返回 True（窗口保持打开）。"""
            raw = {key: entries[key].get() for key, _label, _tip in _FIELD_ROWS}
            result = parse_deband_form(raw)
            if isinstance(result, str):
                messagebox.showerror("无效参数", result, parent=root)
                return False
            job_ref.set_deband(result)
            persist_job_settings(job_ref)
            logging.info("Deband params updated: %s", result.as_settings_dict())
            _trigger_wallpaper_update(job_ref)
            return True

        def _on_apply() -> None:
            _apply_form()

        def _on_ok() -> None:
            if _apply_form():
                _close_window()

        def _on_defaults() -> None:
            _fill(DEFAULT_DEBAND)

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(_FIELD_ROWS), column=0, columnspan=2, pady=(12, 0))
        ttk.Button(buttons, text="恢复默认", command=_on_defaults).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="应用", command=_on_apply).pack(side=tk.LEFT, padx=4)
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

    threading.Thread(target=_run, daemon=True, name="deband-params-dialog").start()
