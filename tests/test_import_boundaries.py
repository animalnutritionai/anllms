"""
Import-boundary enforcement test.

Guarantees the one-directional layering rule established in
anllms/decision/__init__.py: the calculation/citation layers
(knowledge/, scientific/, feed_library/, simulation/) must NEVER import
anything from anllms.decision (evaluate_diet, solve_diet, sensitivity
analysis, etc.). The decision layer is free to import FROM these
layers -- never the reverse.

Why this matters: it's the machine-enforced version of "changes to the
new diet-evaluation/solving code can't corrupt the existing citation
engine, and vice versa." A code review can miss a stray import; this
test can't -- it runs every time the suite runs.

If this test ever fails, the fix is almost always to invert the
dependency (move the shared piece into one of the calculation layers,
or into knowledge/ if it's genuinely shared) -- not to special-case an
exception here.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_PACKAGES = ["knowledge", "scientific", "feed_library", "simulation"]
FORBIDDEN_IMPORT_PREFIX = "anllms.decision"


def _imported_module_names(file_path: Path) -> list[str]:
    """Every dotted module name this file imports, via both
    'import x.y' and 'from x.y import z' forms."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def _all_python_files(package_dir: Path) -> list[Path]:
    return sorted(package_dir.rglob("*.py"))


def test_calculation_layers_never_import_decision_layer():
    violations: list[str] = []

    for package_name in PROTECTED_PACKAGES:
        package_dir = REPO_ROOT / "anllms" / package_name
        if not package_dir.exists():
            continue
        for py_file in _all_python_files(package_dir):
            for module_name in _imported_module_names(py_file):
                if module_name == FORBIDDEN_IMPORT_PREFIX or module_name.startswith(
                    FORBIDDEN_IMPORT_PREFIX + "."
                ):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)} imports '{module_name}'")

    assert not violations, (
        "Calculation/citation layer files must never import from "
        "anllms.decision (the diet evaluation/solving layer). Found:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
