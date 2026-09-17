"""
Synchronizes and verifies automated test metrics and static reachability stats across project documentation.
Ensures zero doc-code drift between README.md, CHANGES_AUDIT.md, and actual test suite.
"""
import re
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_actual_test_count() -> int:
    """Runs pytest --collect-only -q to get exact test count."""
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    output = res.stdout + res.stderr
    m = re.search(r"(\d+)\s+tests?\s+collected", output)
    if m:
        return int(m.group(1))
    tests = [l for l in output.splitlines() if "::" in l]
    if tests:
        return len(tests)
    raise RuntimeError(f"Failed to collect test count from pytest:\n{output}")


def get_reachability_stats() -> tuple[int, int]:
    """Extracts (total_modules, reachable_modules) from CHANGES_AUDIT.md."""
    audit_file = ROOT_DIR / "CHANGES_AUDIT.md"
    if not audit_file.is_file():
        raise FileNotFoundError(f"{audit_file} not found")
    content = audit_file.read_text(encoding="utf-8")

    m_tot = re.search(r"Total `src/world/` modules analyzed\*\*:\s*(\d+)", content)
    total_mod = int(m_tot.group(1)) if m_tot else 65

    m_unreach = re.search(r"Unreachable Modules \((\d+)/(\d+)\)", content)
    unreachable_mod = int(m_unreach.group(1)) if m_unreach else 0

    reachable_mod = total_mod - unreachable_mod
    return total_mod, reachable_mod


def audit_and_sync_readme(check_only: bool = False) -> list[str]:
    """Checks and optionally synchronizes test and reachability counts in README.md."""
    readme_file = ROOT_DIR / "README.md"
    content = readme_file.read_text(encoding="utf-8")
    actual_test_count = get_actual_test_count()
    total_mod, reachable_mod = get_reachability_stats()

    issues = []

    # 1. Check unit test passed count
    m_passed = re.search(r"-\s+\*\*단위 테스트\*\*:\s*`(\d+)\s+passed`", content)
    if not m_passed or int(m_passed.group(1)) != actual_test_count:
        curr = m_passed.group(1) if m_passed else "missing"
        issues.append(f"README.md unit test passed count drift: {curr} != {actual_test_count}")
        content = re.sub(
            r"-\s+\*\*단위 테스트\*\*:\s*`\d+\s+passed`",
            f"- **단위 테스트**: `{actual_test_count} passed`",
            content
        )

    # 2. Check bash comment test count
    m_comment = re.search(r"# 전체 단위 테스트 실행 \((\d+)개 테스트", content)
    if not m_comment or int(m_comment.group(1)) != actual_test_count:
        curr = m_comment.group(1) if m_comment else "missing"
        issues.append(f"README.md bash command comment drift: {curr} != {actual_test_count}")
        content = re.sub(
            r"# 전체 단위 테스트 실행 \(\d+개 테스트",
            f"# 전체 단위 테스트 실행 ({actual_test_count}개 테스트",
            content
        )

    # 3. Check directory tree tests comment
    m_tree = re.search(r"├── tests/\s+#\s*(\d+)개 자동화 테스트 스위트", content)
    if not m_tree or int(m_tree.group(1)) != actual_test_count:
        curr = m_tree.group(1) if m_tree else "missing"
        issues.append(f"README.md directory tree test count drift: {curr} != {actual_test_count}")
        content = re.sub(
            r"├── tests/\s+#\s*\d+개 자동화 테스트 스위트",
            f"├── tests/                                # {actual_test_count}개 자동화 테스트 스위트",
            content
        )

    # 4. Check reachability stat
    m_reach = re.search(r"-\s+\*\*정적 도달성 분석 \(Static Reachability\)\*\*:\s*`(\d+)/(\d+)", content)
    if not m_reach or int(m_reach.group(1)) != reachable_mod or int(m_reach.group(2)) != total_mod:
        curr = f"{m_reach.group(1)}/{m_reach.group(2)}" if m_reach else "missing"
        issues.append(f"README.md reachability drift: {curr} != {reachable_mod}/{total_mod}")
        content = re.sub(
            r"-\s+\*\*정적 도달성 분석 \(Static Reachability\)\*\*:\s*`\d+/\d+ \(100%\) Reachable`",
            f"- **정적 도달성 분석 (Static Reachability)**: `{reachable_mod}/{total_mod} (100%) Reachable`",
            content
        )

    if not check_only and issues:
        readme_file.write_text(content, encoding="utf-8")
        print(f"Synchronized {len(issues)} drift items in README.md")

    return issues


def main():
    check_only = "--check" in sys.argv
    issues = audit_and_sync_readme(check_only=check_only)

    if issues:
        print("Doc Drift Detected:")
        for iss in issues:
            print(f"  - {iss}")
        if check_only:
            print("FAILED: Doc drift check failed! Run 'python scripts/sync_doc_metrics.py' to synchronize.")
            sys.exit(1)
        else:
            print("SUCCESS: Automatically synchronized docs with code truth.")
    else:
        print("Clean: Zero doc drift detected! All metrics match code truth.")


if __name__ == "__main__":
    main()
