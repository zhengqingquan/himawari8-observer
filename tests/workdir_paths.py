"""测试产物根目录：所有会落盘的用例应把 base_dir 指到这里。"""

from __future__ import annotations

import atexit
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

WORKDIR = Path(__file__).resolve().parent / "workdir"
_atexit_registered = False


def _rmdir_workdir_if_empty() -> None:
    """若 tests/workdir 存在且为空则删除（残留临时目录时保留）。"""
    try:
        if WORKDIR.is_dir() and not any(WORKDIR.iterdir()):
            WORKDIR.rmdir()
    except OSError:
        pass


def ensure_workdir() -> Path:
    global _atexit_registered
    WORKDIR.mkdir(parents=True, exist_ok=True)
    if not _atexit_registered:
        atexit.register(_rmdir_workdir_if_empty)
        _atexit_registered = True
    return WORKDIR


@contextmanager
def temporary_base_dir() -> Iterator[Path]:
    """在 tests/workdir/ 下创建临时 base_dir，退出后删除。"""
    ensure_workdir()
    with tempfile.TemporaryDirectory(dir=WORKDIR) as tmp:
        yield Path(tmp)
