import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, deque

ROOT_DIR = Path(__file__).resolve().parent.parent

def resolve_module_path(current_file: Path, module_name: str, level: int = 0) -> Path | None:
    """Resolve an imported module to a file path within ROOT_DIR."""
    if level > 0:
        base_dir = current_file.parent
        for _ in range(level - 1):
            base_dir = base_dir.parent
        if module_name:
            target = base_dir / module_name.replace('.', '/')
        else:
            target = base_dir
    else:
        target = ROOT_DIR / module_name.replace('.', '/')

    if target.with_suffix('.py').is_file():
        return target.with_suffix('.py').resolve()
    init_file = target / '__init__.py'
    if init_file.is_file():
        return init_file.resolve()

    return None

def extract_imports(file_path: Path) -> set[Path]:
    """Parse a python file and extract all imported file paths within ROOT_DIR."""
    imported_files = set()
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return imported_files

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved = resolve_module_path(file_path, alias.name, level=0)
                if resolved and (ROOT_DIR in resolved.parents or resolved == ROOT_DIR):
                    imported_files.add(resolved)
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            resolved = resolve_module_path(file_path, mod_name, level=node.level)
            if resolved:
                imported_files.add(resolved)
            if resolved and resolved.name == '__init__.py':
                pkg_dir = resolved.parent
                for alias in node.names:
                    sub_file = pkg_dir / f"{alias.name}.py"
                    if sub_file.is_file():
                        imported_files.add(sub_file.resolve())

    return imported_files

def get_reachable_files(entrypoints: list[Path]) -> set[Path]:
    """Traverse import graph from entrypoints."""
    reachable = set()
    queue = deque()

    for ep in entrypoints:
        if ep.is_file():
            resolved = ep.resolve()
            reachable.add(resolved)
            queue.append(resolved)

    while queue:
        curr = queue.popleft()
        neighbors = extract_imports(curr)
        for neighbor in neighbors:
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    return reachable

def get_public_definitions(file_path: Path) -> list[str]:
    """Get public function and method names defined in a file."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return []

    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('_'):
                names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith('_'):
                        names.append(item.name)
    return list(dict.fromkeys(names))

def classify_methods(world_files: list[Path], reachable_files: set[Path]):
    all_py_files = list(ROOT_DIR.glob("**/*.py"))
    
    test_files = [f.resolve() for f in all_py_files if 'tests' in f.parts]
    live_files = [f.resolve() for f in all_py_files if 'tests' not in f.parts and f.resolve() in reachable_files]
    non_test_files = [f.resolve() for f in all_py_files if 'tests' not in f.parts]

    live_contents = [(f, f.read_text(encoding='utf-8', errors='ignore')) for f in live_files]
    test_contents = [(f, f.read_text(encoding='utf-8', errors='ignore')) for f in test_files]
    non_test_contents = [(f, f.read_text(encoding='utf-8', errors='ignore')) for f in non_test_files]

    results = {}

    for w_file in world_files:
        w_resolved = w_file.resolve()
        is_reachable = w_resolved in reachable_files
        public_methods = get_public_definitions(w_file)
        
        live_count = 0
        tests_only_count = 0
        never_called_count = 0
        
        method_details = []

        for m_name in public_methods:
            called_in_live = any(
                m_name in content for f, content in live_contents if f != w_resolved
            )
            called_in_tests = any(
                m_name in content for f, content in test_contents
            )
            called_in_non_test = any(
                m_name in content for f, content in non_test_contents if f != w_resolved
            )

            if called_in_live:
                live_count += 1
                status = "called-from-live-path"
            elif called_in_tests:
                tests_only_count += 1
                status = "called-from-tests-only"
            else:
                never_called_count += 1
                status = "never-called"

            method_details.append((m_name, status))

        results[w_file.name] = {
            "reachable": is_reachable,
            "total_methods": len(public_methods),
            "live_count": live_count,
            "tests_only_count": tests_only_count,
            "never_called_count": never_called_count,
            "details": method_details
        }

    return results

def main():
    entrypoints = [
        ROOT_DIR / "app.py",
        ROOT_DIR / "src" / "agents" / "game_master.py"
    ]

    reachable = get_reachable_files(entrypoints)
    world_dir = ROOT_DIR / "src" / "world"
    world_files = sorted([f for f in world_dir.glob("*.py") if f.name != "__init__.py"])

    analysis = classify_methods(world_files, reachable)

    report_path = ROOT_DIR / "CHANGES_AUDIT.md"
    lines = [
        "# CHANGES_AUDIT: Static Reachability and Call Analysis",
        "",
        f"**Entrypoints**: `app.py`, `src/agents/game_master.py`  ",
        f"**Total `src/world/` modules analyzed**: {len(world_files)}  ",
        "",
        "## Summary Table",
        "",
        "| Module | File Reachable? | Total Public Methods | Called-in-Live-Path | Tests-Only | Never-Called |",
        "|---|:---:|:---:|:---:|:---:|:---:|",
    ]

    total_pub = 0
    total_live = 0
    total_tests = 0
    total_never = 0
    unreachable_modules = []

    for mod_name, data in analysis.items():
        reach_str = "✅ Yes" if data["reachable"] else "❌ No"
        if not data["reachable"]:
            unreachable_modules.append(mod_name)
        lines.append(
            f"| `{mod_name}` | {reach_str} | {data['total_methods']} | {data['live_count']} | {data['tests_only_count']} | {data['never_called_count']} |"
        )
        total_pub += data["total_methods"]
        total_live += data["live_count"]
        total_tests += data["tests_only_count"]
        total_never += data["never_called_count"]

    lines.extend([
        f"| **TOTAL** | - | **{total_pub}** | **{total_live}** | **{total_tests}** | **{total_never}** |",
        "",
        f"### Unreachable Modules ({len(unreachable_modules)}/{len(world_files)})",
        "",
    ])

    for m in unreachable_modules:
        lines.append(f"- ❌ `{m}`")

    lines.append("\n## Detailed Method Breakdown\n")
    for mod_name, data in analysis.items():
        if data["tests_only_count"] > 0 or data["never_called_count"] > 0:
            lines.append(f"### `{mod_name}` (Reachable: {data['reachable']})")
            for m_name, status in data["details"]:
                if status != "called-from-live-path":
                    lines.append(f"- `{m_name}`: **{status}**")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Audit complete. Results written to {report_path}")
    print(f"Unreachable modules: {len(unreachable_modules)}/{len(world_files)}")

if __name__ == "__main__":
    main()
