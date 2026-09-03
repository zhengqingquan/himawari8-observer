"""测试产物根目录：所有会落盘的用例应把 base_dir 指到这里。"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

WORKDIR = Path(__file__).resolve().parent / "workdir"


def ensure_workdir() -> Path:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    return WORKDIR


@contextmanager
def temporary_base_dir() -> Iterator[Path]:
    """在 tests/workdir/ 下创建临时 base_dir，退出后删除。"""
    ensure_workdir()
    with tempfile.TemporaryDirectory(dir=WORKDIR) as tmp:
        yield Path(tmp)
