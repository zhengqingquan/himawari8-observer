"""Architecture seam: UI and scheduler must not import pipeline/dl internals."""

import ast
import unittest
from pathlib import Path


_FORBIDDEN_IMPORT_PREFIXES = (
    "src.wallpaper_pipeline",
    "src.download",
    "src.compose",
    "src.pic",
)

_GUARDED_FILES = (
    Path("src/tray/sysTray.py"),
    Path("src/timetask.py"),
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class SeamImportGuardTests(unittest.TestCase):
    def test_ui_and_scheduler_stay_above_pipeline(self):
        root = Path(__file__).resolve().parents[1]
        for rel in _GUARDED_FILES:
            path = root / rel
            imported = _imported_modules(path)
            offenders = {
                name
                for name in imported
                if any(
                    name == prefix or name.startswith(prefix + ".")
                    for prefix in _FORBIDDEN_IMPORT_PREFIXES
                )
            }
            self.assertEqual(
                offenders,
                set(),
                f"{rel} must not import pipeline/dl internals, found {offenders}",
            )


if __name__ == "__main__":
    unittest.main()
