"""Unit tests for ReportBuilder.

Requirements covered: REQ-GEN-01, REQ-GEN-02, REQ-GEN-03, REQ-GEN-04
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from generate_release_notes import ReportBuilder
from release_notes_schema import EXECUTIVE_REPORT_SCHEMA, validate_report

ROOT = Path(__file__).parent.parent.parent


def make_builder(tag="test-v1.0.0"):
    return ReportBuilder(
        owner="test-org",
        repo="test-repo",
        release_tag=tag,
        commit_sha="abc1234",
    )


def test_executive_report_without_inputs():
    """REQ-GEN-01/02: ReportBuilder produces a report dict with no test inputs."""
    report = make_builder().build_executive_report(None, None, None)
    assert report["report_type"] == "executive-report"
    assert isinstance(report["requirements"], list)
    assert isinstance(report["test_suites"], list)


def test_executive_report_contains_release_tag():
    """REQ-GEN-03: The release tag supplied at construction appears in the report."""
    report = make_builder("staging-v2.3.0").build_executive_report(None, None, None)
    assert report["repository"]["release_tag"] == "staging-v2.3.0"


def test_executive_report_conforms_to_schema():
    """REQ-GEN-04: The generated report passes schema validation."""
    report = make_builder().build_executive_report(None, None, None)
    errors = validate_report(report, EXECUTIVE_REPORT_SCHEMA)
    assert errors == [], f"Schema validation failed: {errors}"


def test_executive_report_summary_zero_pass_rate_with_no_tests():
    """REQ-GEN-01: pass_rate is 0.0 when no tests are provided."""
    report = make_builder().build_executive_report(None, None, None)
    assert report["summary"]["pass_rate"] == 0.0
    assert report["summary"]["total_scenarios"] == 0


def test_cli_produces_json_file(tmp_path):
    """REQ-GEN-01: The CLI script writes executive-report.json to --output-dir."""
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_release_notes.py"),
            "--output-dir", str(tmp_path),
            "--owner", "test-org",
            "--repo", "test-repo",
            "--release-tag", "cli-v0.1.0",
            "--commit", "deadbeef",
        ],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": f"{ROOT}{__import__('os').pathsep}{ROOT / 'examples'}"},
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "executive-report.json").exists()


def test_cli_produces_html_file(tmp_path):
    """REQ-GEN-02: The CLI script writes executive-report.html to --output-dir."""
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_release_notes.py"),
            "--output-dir", str(tmp_path),
            "--owner", "test-org",
            "--repo", "test-repo",
            "--release-tag", "cli-v0.1.0",
            "--commit", "deadbeef",
        ],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": f"{ROOT}{__import__('os').pathsep}{ROOT / 'examples'}"},
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "executive-report.html").exists()


def test_cli_json_contains_release_tag(tmp_path):
    """REQ-GEN-03: The JSON output contains the release tag passed on the CLI."""
    tag = "pre-release-registry-v0.9.0-rc"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_release_notes.py"),
            "--output-dir", str(tmp_path),
            "--owner", "test-org",
            "--repo", "test-repo",
            "--release-tag", tag,
            "--commit", "deadbeef",
        ],
        check=True,
        capture_output=True,
        env={**__import__("os").environ, "PYTHONPATH": f"{ROOT}{__import__('os').pathsep}{ROOT / 'examples'}"},
    )
    report = json.loads((tmp_path / "executive-report.json").read_text())
    assert report["repository"]["release_tag"] == tag


def test_html_groups_requirements_by_phase(monkeypatch):
    """REQ-PHASE-04: HTML renders phase sections ascending (MVP before Phase 2),
    grouping each requirement by its own phase."""
    import silverline.reporting.generate as g
    from silverline.reporting.manifest import Requirement
    from silverline.reporting.phases import Phase

    monkeypatch.setattr(g, "CATEGORIES", {
        "AUTH": {"name": "Auth", "description": "d", "phase": 0, "order": 1},
    })
    monkeypatch.setattr(g, "NORM_REQUIREMENTS", {
        "AUTH-01": Requirement("AUTH-01", "MVP req", "P0", "Implemented", Phase.MVP, "AUTH"),
        "AUTH-09": Requirement("AUTH-09", "Later req", "P1", "Planned", Phase.PHASE_2, "AUTH"),
    })
    builder = make_builder()
    report = builder.build_executive_report(None, None, None)
    html = builder.build_executive_html(report, None)
    assert "MVP" in html and "Phase 2" in html
    assert html.index("MVP") < html.index("Phase 2")
    assert "AUTH-01" in html and "AUTH-09" in html
