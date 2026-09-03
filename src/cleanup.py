"""设壁纸成功后清理本地影像缓存：保留当前壁纸文件。"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path


def cleanup_after_wallpaper_apply(
    *,
    img_root: Path,
    current_run_root: Path,
    keep_file: Path,
) -> None:
    """保留 keep_file，删除本次瓦片与多余中间图，并清掉其它旧观测目录。

    删除失败只记日志，不向外抛。

    Args:
        img_root: 影像缓存根目录（通常为 ``.../img``）。
        current_run_root: 本次观测时间对应的运行目录。
        keep_file: 设壁纸后需保留的文件（须位于 img_root 下）。
    """
    try:
        img_root = img_root.resolve()
        current_run_root = current_run_root.resolve()
        keep_file = keep_file.resolve()
    except OSError as exc:
        logging.warning("清理缓存：解析路径失败：%s", exc)
        return

    if not img_root.is_dir():
        logging.info("清理缓存：img 根目录不存在，跳过：%s", img_root)
        return

    try:
        current_run_root.relative_to(img_root)
        keep_file.relative_to(img_root)
    except ValueError:
        logging.warning(
            "清理缓存：路径不在 img 下，跳过（img=%s run=%s keep=%s）",
            img_root,
            current_run_root,
            keep_file,
        )
        return

    _delete_sibling_run_dirs(img_root, current_run_root)
    _delete_tile_trees(current_run_root)
    _delete_extra_complete_files(current_run_root, keep_file)
    logging.info("清理缓存完成：保留 %s", keep_file)


def _delete_sibling_run_dirs(img_root: Path, current_run_root: Path) -> None:
    for child in img_root.iterdir():
        if not child.is_dir():
            continue
        try:
            if child.resolve() == current_run_root:
                continue
        except OSError:
            continue
        _rmtree(child)


def _delete_tile_trees(current_run_root: Path) -> None:
    if not current_run_root.is_dir():
        return
    for child in current_run_root.iterdir():
        if child.is_dir() and child.name != "complete":
            _rmtree(child)


def _delete_extra_complete_files(current_run_root: Path, keep_file: Path) -> None:
    complete = current_run_root / "complete"
    if not complete.is_dir():
        return
    for path in complete.iterdir():
        if not path.is_file():
            continue
        try:
            if path.resolve() == keep_file:
                continue
        except OSError:
            continue
        _unlink(path)


def _rmtree(path: Path) -> None:
    try:
        shutil.rmtree(path)
        logging.info("已删除目录：%s", path)
    except OSError as exc:
        logging.warning("删除目录失败：%s (%s)", path, exc)


def _unlink(path: Path) -> None:
    try:
        path.unlink()
        logging.info("已删除文件：%s", path)
    except OSError as exc:
        logging.warning("删除文件失败：%s (%s)", path, exc)
