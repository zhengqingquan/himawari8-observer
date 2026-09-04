"""设壁纸成功后清理本地影像缓存：保留当前壁纸文件。"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterable
from pathlib import Path


def cleanup_after_wallpaper_apply(
    *,
    img_root: Path,
    current_run_root: Path,
    keep_file: Path | None = None,
    keep_files: Iterable[Path] | None = None,
) -> None:
    """保留 keep 文件，删除本次瓦片与多余中间图，并清掉其它旧观测目录。

    删除失败只记日志，不向外抛。

    Args:
        img_root: 影像缓存根目录（通常为 ``.../img``）。
        current_run_root: 本次观测时间对应的运行目录。
        keep_file: 单个需保留的文件（兼容旧调用）。
        keep_files: 额外或批量需保留的文件（须位于 img_root 下）。
    """
    paths: list[Path] = []
    if keep_file is not None:
        paths.append(keep_file)
    if keep_files is not None:
        paths.extend(keep_files)
    if not paths:
        logging.warning("Cleanup skipped: no keep_file(s) provided")
        return

    try:
        img_root = img_root.resolve()
        current_run_root = current_run_root.resolve()
        keep_resolved: set[Path] = set()
        for path in paths:
            keep_resolved.add(path.resolve())
    except OSError:
        logging.exception(
            "Cleanup skipped: failed to resolve paths (img=%s run=%s keep=%s)",
            img_root,
            current_run_root,
            paths,
        )
        return

    if not img_root.is_dir():
        logging.info("Cleanup skipped: img root does not exist: %s", img_root)
        return

    try:
        current_run_root.relative_to(img_root)
        for keep in keep_resolved:
            keep.relative_to(img_root)
    except ValueError:
        logging.warning(
            "Cleanup skipped: path outside img root (img=%s run=%s keep=%s)",
            img_root,
            current_run_root,
            keep_resolved,
        )
        return

    _delete_sibling_run_dirs(img_root, current_run_root)
    _delete_tile_trees(current_run_root)
    _delete_extra_complete_files(current_run_root, keep_resolved)
    logging.info("Cleanup finished; kept wallpaper file(s): %s", sorted(str(p) for p in keep_resolved))


def _delete_sibling_run_dirs(img_root: Path, current_run_root: Path) -> None:
    for child in img_root.iterdir():
        if not child.is_dir():
            continue
        try:
            if child.resolve() == current_run_root:
                continue
        except OSError:
            logging.warning("Cleanup: failed to resolve sibling run dir: %s", child, exc_info=True)
            continue
        _rmtree(child)


def _delete_tile_trees(current_run_root: Path) -> None:
    if not current_run_root.is_dir():
        logging.warning("Cleanup: current run root is not a directory: %s", current_run_root)
        return
    for child in current_run_root.iterdir():
        if child.is_dir() and child.name != "complete":
            _rmtree(child)


def _delete_extra_complete_files(current_run_root: Path, keep_files: set[Path]) -> None:
    complete = current_run_root / "complete"
    if not complete.is_dir():
        return
    for path in complete.iterdir():
        if not path.is_file():
            continue
        try:
            if path.resolve() in keep_files:
                continue
        except OSError:
            logging.warning("Cleanup: failed to resolve compose file: %s", path, exc_info=True)
            continue
        _unlink(path)


def _rmtree(path: Path) -> None:
    try:
        shutil.rmtree(path)
        logging.info("Deleted directory: %s", path)
    except OSError as exc:
        logging.warning("Failed to delete directory %s: %s", path, exc)


def _unlink(path: Path) -> None:
    try:
        path.unlink()
        logging.info("Deleted file: %s", path)
    except OSError as exc:
        logging.warning("Failed to delete file %s: %s", path, exc)
