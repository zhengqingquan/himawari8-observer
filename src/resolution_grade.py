"""分辨率档位：瓦片边长、Nd 网格与像素边长的唯一映射。"""

from __future__ import annotations

_TILE_PIXEL = 550
_DEFAULT_GRADE = "4d"
_GRADE_TO_GRID: dict[str, int] = {
    "1d": 1,
    "4d": 4,
    "8d": 8,
    "16d": 16,
    "20d": 20,
}
_PIXEL_TO_GRADE: dict[int, str] = {
    _TILE_PIXEL * grid: grade for grade, grid in _GRADE_TO_GRID.items()
}


def tile_pixel() -> int:
    return _TILE_PIXEL


def default_grade() -> str:
    return _DEFAULT_GRADE


def grade_to_grid(grade: str) -> int:
    try:
        return _GRADE_TO_GRID[grade]
    except KeyError as exc:
        raise ValueError(f"unknown resolution grade: {grade!r}") from exc


def pixel_to_grade(pixel_side: int) -> str:
    try:
        return _PIXEL_TO_GRADE[pixel_side]
    except KeyError as exc:
        raise ValueError(f"unknown resolution pixel side: {pixel_side!r}") from exc


def supported_pixels() -> list[int]:
    return sorted(_PIXEL_TO_GRADE)


def grade_to_pixel(grade: str) -> int:
    return tile_pixel() * grade_to_grid(grade)
