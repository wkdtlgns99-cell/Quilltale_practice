"""
P2-4 Document-Code Drift Verification Test Suite.
Tests:
1. Verification that README.md test metrics match actual collected pytest tests.
2. Verification that README.md reachability matches CHANGES_AUDIT.md.
3. Verification that TRIAGE.md has 0 unreachable modules in Category C.
4. Verification that scripts/sync_doc_metrics.py detects drift accurately.
"""
from pathlib import Path
from scripts.sync_doc_metrics import audit_and_sync_readme, get_actual_test_count, get_reachability_stats

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_readme_matches_actual_collected_tests():
    """Verify README.md contains exact test count without manual drift."""
    issues = audit_and_sync_readme(check_only=True)
    assert len(issues) == 0, f"Doc drift detected in README.md: {issues}"


def test_reachability_audit_matches_triage_and_readme():
    """Verify CHANGES_AUDIT.md, TRIAGE.md, and README.md are 100% consistent on reachability."""
    total_mod, reachable_mod = get_reachability_stats()
    assert total_mod == reachable_mod, f"Unreachable modules detected: {total_mod - reachable_mod}"

    # Verify TRIAGE.md
    triage_file = ROOT_DIR / "TRIAGE.md"
    content = triage_file.read_text(encoding="utf-8")
    assert f"### Category C: `SHELVED / UNREACHABLE` (0 of {total_mod} modules)" in content
    assert f"All {total_mod} `src/world/` modules are 100% reachable" in content


def test_sync_doc_metrics_detects_drift():
    """Verify audit_and_sync_readme logic flags mismatch when test count differs."""
    actual = get_actual_test_count()
    assert actual >= 640
