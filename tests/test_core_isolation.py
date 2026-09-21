"""core 的依赖边界：通用包不得引入框架依赖，也不得反向依赖 web / gui。

不用运行时断言（`sys.modules` 检查）是有原因的：开发环境通常把 extras 装齐了，
fastapi / PySide6 本来就可达，那种断言在这里必然失败、只能扔进单独一条 CI 流水线。
静态扫 import 则是同一个 venv 里就能跑的等价约束，且报错能直接指到文件。
"""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "fdy"
CORE = PACKAGE_ROOT / "core"

FRAMEWORK_ROOTS = {"fastapi", "starlette", "PySide6", "shiboken6"}
FORBIDDEN_FDY_SUBPACKAGES = {"fdy.web", "fdy.gui"}


def _absolute_import(path: Path, node: ast.ImportFrom, package_root: Path) -> str:
    """把 `from ...gui import x` 这类相对导入解析成绝对模块名。"""
    if not node.level:
        return node.module or ""
    package = ["fdy", *path.relative_to(package_root).parts[:-1]]
    head = package[: len(package) - (node.level - 1)]
    tail = (node.module or "").split(".") if node.module else []
    return ".".join([*head, *tail])


def _violations(path: Path, package_root: Path) -> list[str]:
    tree = ast.parse(path.read_text("utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [_absolute_import(path, node, package_root)]
        else:
            continue
        for module in modules:
            is_framework = module.split(".")[0] in FRAMEWORK_ROOTS
            is_sibling = any(
                module == sub or module.startswith(f"{sub}.")
                for sub in FORBIDDEN_FDY_SUBPACKAGES
            )
            if is_framework or is_sibling:
                found.append(module)
    return found


def test_core_imports_no_frameworks_and_no_sibling_subpackages():
    leaks = {
        str(path.relative_to(CORE)): bad
        for path in sorted(CORE.rglob("*.py"))
        if (bad := _violations(path, PACKAGE_ROOT))
    }

    assert leaks == {}, f"core 越界导入了框架或 web/gui：{leaks}"


def test_scanner_detects_the_patterns_it_claims_to_detect(tmp_path):
    """自证扫描器有效：绝对导入与相对导入两种越界写法都能认出来。"""
    package_root = tmp_path / "fdy"
    probe = package_root / "core" / "utils" / "probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text(
        "import fastapi\nfrom fdy.gui import chain\nfrom ...gui import signals\n",
        encoding="utf-8",
    )
    clean = package_root / "core" / "clean.py"
    clean.write_text("from .._optional import require\nimport json\n", encoding="utf-8")

    assert _violations(probe, package_root) == ["fastapi", "fdy.gui", "fdy.gui"]
    assert _violations(clean, package_root) == []
