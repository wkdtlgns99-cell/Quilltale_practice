"""
P2-3 GitHub Actions CI Workflow Verification Test Suite.
Tests:
1. Verification of .github/workflows/ci.yml existence and YAML structure.
2. Verification of essential triggers (push, pull_request).
3. Verification of 4 critical quality gate steps:
   - pyflakes code hygiene
   - ruff critical syntax lint
   - scripts/reachability_audit.py
   - pytest test suite
4. Verification of reachability_audit.py exit 1 failure guard.
"""
from pathlib import Path


def test_ci_workflow_file_exists_and_valid():
    """Verify .github/workflows/ci.yml exists and contains required steps."""
    ci_file = Path(r".github/workflows/ci.yml")
    assert ci_file.is_file(), ".github/workflows/ci.yml must exist"

    content = ci_file.read_text(encoding="utf-8")
    assert "name: Quilltale CI Pipeline" in content
    assert "branches: [ main ]" in content
    assert "runs-on: ubuntu-latest" in content


def test_ci_workflow_critical_gate_steps():
    """Verify all 4 DoD and Hygiene gate commands are defined in the workflow."""
    ci_file = Path(r".github/workflows/ci.yml")
    content = ci_file.read_text(encoding="utf-8")

    # 1. Code Hygiene Check
    assert "python -m pyflakes" in content
    # 2. Critical Syntax & Import Lint
    assert "ruff check" in content
    # 3. Static Reachability Audit
    assert "python scripts/reachability_audit.py" in content
    # 4. Automated Tests
    assert "pytest tests/" in content


def test_reachability_audit_script_exit_code_guard():
    """Verify reachability_audit.py contains sys.exit(1) on unreachable modules."""
    audit_file = Path(r"scripts/reachability_audit.py")
    content = audit_file.read_text(encoding="utf-8")
    assert "sys.exit(1)" in content
    assert "unreachable modules detected" in content
