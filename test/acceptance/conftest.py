"""
Shared fixtures and step definitions for all acceptance scenarios.

Steps are organised by feature area but all live here so pytest-bdd can share
them across scenario files without duplication.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, then, when

ROOT = Path(__file__).parent.parent.parent
PYTHON = sys.executable


# ── Shared context fixture ─────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    """Mutable dict shared between steps within a scenario."""
    return {}


# ── Manifest fixture (installs example manifest into scripts/ temporarily) ────

@pytest.fixture
def with_manifest():
    """Ensure scripts/requirements_manifest.py exists for the duration of the test.

    If a real manifest is already in place (as in this repo), it is left
    untouched after the test. If it doesn't exist, the example is copied in
    and removed on teardown.
    """
    src = ROOT / "examples" / "requirements_manifest.py"
    dst = ROOT / "scripts" / "requirements_manifest.py"
    pre_existing = dst.exists()
    if not pre_existing:
        shutil.copy(src, dst)
    yield dst
    if not pre_existing:
        dst.unlink(missing_ok=True)


# ── Report Generation steps ───────────────────────────────────────────────────

@given("the report generator script is available")
def generator_available():
    assert (ROOT / "scripts" / "generate_release_notes.py").exists()


@when("I run the generator with a release tag and an output directory")
def run_generator(ctx, tmp_path):
    result = subprocess.run(
        [
            PYTHON,
            str(ROOT / "scripts" / "generate_release_notes.py"),
            "--output-dir", str(tmp_path / "release"),
            "--owner", "test-org",
            "--repo", "test-repo",
            "--release-tag", "acc-v1.0.0",
            "--commit", "deadbeef",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "examples")},
    )
    ctx["returncode"] = result.returncode
    ctx["output_dir"] = tmp_path / "release"
    assert result.returncode == 0, result.stderr


@when(parsers.parse('I run the generator with release tag "{tag}"'))
def run_generator_with_tag(ctx, tmp_path, tag):
    result = subprocess.run(
        [
            PYTHON,
            str(ROOT / "scripts" / "generate_release_notes.py"),
            "--output-dir", str(tmp_path / "release"),
            "--owner", "test-org",
            "--repo", "test-repo",
            "--release-tag", tag,
            "--commit", "deadbeef",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "examples")},
    )
    ctx["returncode"] = result.returncode
    ctx["output_dir"] = tmp_path / "release"
    ctx["tag"] = tag
    assert result.returncode == 0, result.stderr


@then("executive-report.json is created in the output directory")
def json_created(ctx):
    assert (ctx["output_dir"] / "executive-report.json").exists()


@then("executive-report.html is created in the output directory")
def html_created(ctx):
    assert (ctx["output_dir"] / "executive-report.html").exists()


@then(parsers.parse('the executive-report.json release_tag equals "{tag}"'))
def json_has_tag(ctx, tag):
    report = json.loads((ctx["output_dir"] / "executive-report.json").read_text())
    assert report["repository"]["release_tag"] == tag


@then("the executive-report.json passes schema validation")
def json_passes_schema(ctx):
    from release_notes_schema import EXECUTIVE_REPORT_SCHEMA, validate_report
    report = json.loads((ctx["output_dir"] / "executive-report.json").read_text())
    errors = validate_report(report, EXECUTIVE_REPORT_SCHEMA)
    assert errors == [], f"Schema errors: {errors}"


# ── Schema Validation steps ───────────────────────────────────────────────────

_VALID_REPORT = {
    "schema_version": "1.0.0",
    "report_type": "executive-report",
    "generated_at": "2024-01-01T00:00:00+00:00",
    "repository": {"owner": "a", "name": "b", "release_tag": "v1", "commit_sha": "c"},
    "summary": {
        "total_scenarios": 5,
        "passed": 5,
        "failed": 0,
        "skipped": 0,
        "pass_rate": 100.0,
        "overall_status": "passing",
    },
    "requirements": [],
    "test_suites": [],
}


@given("a structurally complete executive report")
def complete_report(ctx):
    ctx["report"] = dict(_VALID_REPORT)


@given("an executive report with the summary field removed")
def report_missing_summary(ctx):
    ctx["report"] = {k: v for k, v in _VALID_REPORT.items() if k != "summary"}


@given("a structurally complete executive report with an integer pass_rate")
def report_with_int_pass_rate(ctx):
    ctx["report"] = {
        **_VALID_REPORT,
        "summary": {**_VALID_REPORT["summary"], "pass_rate": 100},
    }


@when("I validate the report against the schema")
def validate_report_step(ctx):
    from release_notes_schema import EXECUTIVE_REPORT_SCHEMA, validate_report
    ctx["errors"] = validate_report(ctx["report"], EXECUTIVE_REPORT_SCHEMA)


@then("no validation errors are returned")
def no_errors(ctx):
    assert ctx["errors"] == [], f"Unexpected errors: {ctx['errors']}"


@then(parsers.parse('a validation error mentioning "{field}" is returned'))
def error_mentions_field(ctx, field):
    assert ctx["errors"], "Expected at least one error"
    assert any(field in e for e in ctx["errors"]), (
        f'No error mentions "{field}". Errors: {ctx["errors"]}'
    )


# ── Gherkin Parsing steps ─────────────────────────────────────────────────────

_FEATURE_CONTENT = """\
Feature: User authentication

@req-AUTH-01 @story-1-1
Scenario: User registers with valid credentials
  Given the registration page is open
  When the user submits valid registration details
  Then their account is created

@FR-AUTH-02
Scenario: User logs in
  Given the user has an account
  When they log in with valid credentials
  Then they are redirected to the dashboard
"""


@given("a feature file containing two scenarios")
def feature_file(ctx, tmp_path):
    (tmp_path / "auth.feature").write_text(_FEATURE_CONTENT)
    ctx["feature_dir"] = tmp_path


@when("I parse the feature directory")
def parse_feature_dir(ctx):
    from generate_release_notes import GherkinParser
    ctx["features"] = GherkinParser().parse_dir(ctx["feature_dir"])


@then("both scenario names appear in the parsed results")
def both_names_present(ctx):
    names = [s["name"] for feat in ctx["features"] for s in feat["scenarios"]]
    assert "User registers with valid credentials" in names
    assert "User logs in" in names


@then(parsers.parse('the req_tags include "{tag}"'))
def req_tags_include(ctx, tag):
    all_tags = [t for feat in ctx["features"] for s in feat["scenarios"] for t in s["req_tags"]]
    assert tag in all_tags, f'"{tag}" not found in req_tags: {all_tags}'


@then("the steps contain the Given When and Then keywords")
def steps_contain_keywords(ctx):
    keywords = {
        step["keyword"]
        for feat in ctx["features"]
        for s in feat["scenarios"]
        for step in s["steps"]
    }
    assert "Given" in keywords
    assert "When" in keywords
    assert "Then" in keywords


# ── Make Target steps ─────────────────────────────────────────────────────────

@given("the project Makefile is present")
def makefile_present():
    assert (ROOT / "Makefile").exists()


@given("a requirements manifest is installed in scripts")
def manifest_installed(ctx, with_manifest):
    ctx["manifest_path"] = with_manifest


@when("I run make generate-example with a temporary output directory")
def run_make_generate_example(ctx, tmp_path):
    out = tmp_path / "release"
    result = subprocess.run(
        ["make", "-C", str(ROOT), "generate-example", f"OUTPUT_DIR={out}"],
        capture_output=True,
        text=True,
    )
    ctx["returncode"] = result.returncode
    ctx["output_dir"] = out
    ctx["stderr"] = result.stderr


@when("I run make validate")
def run_make_validate(ctx):
    result = subprocess.run(
        ["make", "-C", str(ROOT), "validate"],
        capture_output=True,
        text=True,
    )
    ctx["returncode"] = result.returncode
    ctx["stderr"] = result.stderr


@when("I run make lint")
def run_make_lint(ctx):
    result = subprocess.run(
        ["make", "-C", str(ROOT), "lint"],
        capture_output=True,
        text=True,
    )
    ctx["returncode"] = result.returncode
    ctx["stderr"] = result.stderr


@then("executive-report.json exists in the output directory")
def make_json_exists(ctx):
    assert (ctx["output_dir"] / "executive-report.json").exists()


@then("executive-report.html exists in the output directory")
def make_html_exists(ctx):
    assert (ctx["output_dir"] / "executive-report.html").exists()


@then("the make command exits with code 0")
def make_exits_zero(ctx):
    assert ctx["returncode"] == 0, f"Command failed:\n{ctx.get('stderr', '')}"


# ── Firebase Site Provisioning steps ─────────────────────────────────────────

def _make_mock_firebase(tmp_path, script: str) -> Path:
    """Write a mock firebase executable to tmp_path/bin/ and return the bin dir."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fb = bin_dir / "firebase"
    fb.write_text(f"#!/usr/bin/env bash\n{script}\n")
    fb.chmod(0o755)
    return bin_dir


@given("the Firebase site provisioning script is available")
def provisioning_script_available():
    assert (ROOT / "scripts" / "ensure_firebase_site.sh").exists()


@given("a mock firebase that successfully creates the site")
def mock_firebase_creates(ctx, tmp_path):
    ctx["mock_bin"] = _make_mock_firebase(
        tmp_path, 'echo "Site created successfully"\nexit 0'
    )


@given("a mock firebase that reports the site already exists")
def mock_firebase_exists(ctx, tmp_path):
    ctx["mock_bin"] = _make_mock_firebase(
        tmp_path, 'echo "Error: Site already exists" >&2\nexit 1'
    )


@given("a mock firebase that reports an authentication error")
def mock_firebase_auth_error(ctx, tmp_path):
    ctx["mock_bin"] = _make_mock_firebase(
        tmp_path, 'echo "Error: Authentication failed — check credentials" >&2\nexit 1'
    )


@when(parsers.parse('I run the provisioning script for project "{project}" site "{site}"'))
def run_provisioning_script(ctx, project, site):
    env = {**os.environ, "PATH": str(ctx["mock_bin"]) + ":" + os.environ["PATH"]}
    result = subprocess.run(
        ["bash", str(ROOT / "scripts" / "ensure_firebase_site.sh"), project, site],
        capture_output=True,
        text=True,
        env=env,
    )
    ctx["returncode"] = result.returncode
    ctx["output"] = result.stdout + result.stderr


@then("the script exits with code 0")
def script_exits_zero(ctx):
    assert ctx["returncode"] == 0, f"Script failed:\n{ctx['output']}"


@then("the script exits with a non-zero code")
def script_exits_nonzero(ctx):
    assert ctx["returncode"] != 0, "Expected non-zero exit but script succeeded"


@then(parsers.parse('the output contains "{text}"'))
def output_contains(ctx, text):
    assert text in ctx["output"], f'"{text}" not found in output:\n{ctx["output"]}'
