"""Unit tests for release_notes_schema.validate_report.

Requirements covered: REQ-SCHEMA-01, REQ-SCHEMA-02, REQ-SCHEMA-03
"""
import pytest
from release_notes_schema import EXECUTIVE_REPORT_SCHEMA, validate_report

VALID_REPORT = {
    "schema_version": "1.0.0",
    "report_type": "executive-report",
    "generated_at": "2024-01-01T00:00:00+00:00",
    "repository": {
        "owner": "acme",
        "name": "my-repo",
        "release_tag": "v1.0.0",
        "commit_sha": "abc1234",
    },
    "summary": {
        "total_scenarios": 10,
        "passed": 10,
        "failed": 0,
        "skipped": 0,
        "pass_rate": 100.0,
        "overall_status": "passing",
    },
    "requirements": [],
    "test_suites": [],
}


def test_valid_report_has_no_errors():
    """REQ-SCHEMA-01: No errors for a structurally valid report."""
    errors = validate_report(VALID_REPORT, EXECUTIVE_REPORT_SCHEMA)
    assert errors == []


def test_missing_key_reported_as_error():
    """REQ-SCHEMA-02: Missing required key produces a validation error."""
    incomplete = {k: v for k, v in VALID_REPORT.items() if k != "summary"}
    errors = validate_report(incomplete, EXECUTIVE_REPORT_SCHEMA)
    assert errors, "Expected at least one error"
    assert any("summary" in e for e in errors)


def test_missing_nested_key_reported_as_error():
    """REQ-SCHEMA-02: Missing nested key inside repository produces an error."""
    bad_repo = {**VALID_REPORT["repository"]}
    del bad_repo["release_tag"]
    report = {**VALID_REPORT, "repository": bad_repo}
    errors = validate_report(report, EXECUTIVE_REPORT_SCHEMA)
    assert any("release_tag" in e for e in errors)


def test_int_accepted_where_float_expected():
    """REQ-SCHEMA-03: Integer pass_rate is accepted where float is expected."""
    report = {**VALID_REPORT, "summary": {**VALID_REPORT["summary"], "pass_rate": 100}}
    errors = validate_report(report, EXECUTIVE_REPORT_SCHEMA)
    assert errors == []
