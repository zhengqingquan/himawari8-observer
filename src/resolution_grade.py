"""分辨率档位：瓦片边长、Nd 网格与像素边长的唯一映射。"""

from __future__ import annotations

_TILE_PIXEL = 550
_DEFAULT_GRADE = "4d"
# 渐进更新预览边长（4d）；目标高于此值时先预览再拉目标档。
PROGRESSIVE_PREVIEW_PIXEL = 2200
_GRADE_TO_GRID: dict[str, int] = {
    "1d": 1,
    "2d": 2,
    "4d": 4,
    "8d": 8,
    "16d": 16,
    "20d": 20,
}
_PIXEL_TO_GRADE: dict[int, str] = {
    _TILE_PIXEL * grid: grade for grade, grid in _GRADE_TO_GRID.items()
}


def tile_pixel() -> int:
    """单瓦片边长（像素）。"""
    return _TILE_PIXEL


def default_grade() -> str:
    """真路径默认分辨率档位。"""
    return _DEFAULT_GRADE


def progressive_preview_grade() -> str:
    """渐进更新预览档位（对应 ``PROGRESSIVE_PREVIEW_PIXEL``）。"""
    return pixel_to_grade(PROGRESSIVE_PREVIEW_PIXEL)


def grade_to_grid(grade: str) -> int:
    """档位字符串 → 网格边长（如 ``4d`` → 4）。"""
    try:
        return _GRADE_TO_GRID[grade]
    except KeyError as exc:
        raise ValueError(f"unknown resolution grade: {grade!r}") from exc


def pixel_to_grade(pixel_side: int) -> str:
    """合成图边长（像素）→ 档位字符串。"""
    try:
        return _PIXEL_TO_GRADE[pixel_side]
    except KeyError as exc:
        raise ValueError(f"unknown resolution pixel side: {pixel_side!r}") from exc


def supported_pixels() -> list[int]:
    """已支持的合成图边长列表（升序）。"""
    return sorted(_PIXEL_TO_GRADE)


def grade_to_pixel(grade: str) -> int:
    """档位 → 合成图边长（像素）。"""
    return tile_pixel() * grade_to_grid(grade)
