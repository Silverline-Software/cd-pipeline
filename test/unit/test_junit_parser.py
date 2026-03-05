"""Unit tests for JUnitParser.

Requirements covered: REQ-PARSE-04, REQ-PARSE-05
"""
import pytest
from generate_release_notes import JUnitParser

JUNIT_XML = """\
<?xml version="1.0" ?>
<testsuites>
  <testsuite name="bdd-tests" tests="3" failures="1" errors="0" skipped="0">
    <testcase classname="tests.acceptance" name="test_user_can_register" time="0.5"/>
    <testcase classname="tests.acceptance" name="test_user_can_log_in" time="0.3">
      <failure message="AssertionError: expected True got False"/>
    </testcase>
    <testcase classname="tests.acceptance" name="test_user_can_log_out" time="0.2"/>
  </testsuite>
</testsuites>
"""

JUNIT_XML_SKIPPED = """\
<?xml version="1.0" ?>
<testsuites>
  <testsuite name="suite" tests="2" failures="0" errors="0" skipped="1">
    <testcase classname="tests" name="test_a" time="0.1"/>
    <testcase classname="tests" name="test_b" time="0.0">
      <skipped message="not implemented"/>
    </testcase>
  </testsuite>
</testsuites>
"""


@pytest.fixture
def junit_file(tmp_path):
    f = tmp_path / "results.xml"
    f.write_text(JUNIT_XML)
    return f


def test_junit_parser_extracts_totals(junit_file):
    """REQ-PARSE-04: Total, passed, and failed counts are extracted."""
    results = JUnitParser().parse(junit_file)
    assert results["total"] == 3
    assert results["passed"] == 2
    assert results["failed"] == 1


def test_junit_parser_extracts_skipped(tmp_path):
    """REQ-PARSE-04: Skipped test count is extracted."""
    f = tmp_path / "results.xml"
    f.write_text(JUNIT_XML_SKIPPED)
    results = JUnitParser().parse(f)
    assert results["skipped"] == 1
    assert results["passed"] == 1


def test_junit_parser_testcase_status(junit_file):
    """REQ-PARSE-04: Individual testcase status is correct."""
    results = JUnitParser().parse(junit_file)
    cases = results["suites"][0]["testcases"]
    by_name = {c["name"]: c["status"] for c in cases}
    assert by_name["test_user_can_register"] == "passed"
    assert by_name["test_user_can_log_in"] == "failed"


@pytest.mark.parametrize("name,expected", [
    ("User can register", "test_user_can_register"),
    ("User logs in!", "test_user_logs_in"),
    ("Reset password via email", "test_reset_password_via_email"),
    ("  leading spaces  ", "test_leading_spaces"),
])
def test_junit_parser_scenario_name_mapping(name, expected):
    """REQ-PARSE-05: Scenario names are converted to pytest function names."""
    assert JUnitParser.scenario_to_test_name(name) == expected
