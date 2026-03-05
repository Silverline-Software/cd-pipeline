"""Unit tests for GherkinParser.

Requirements covered: REQ-PARSE-01, REQ-PARSE-02, REQ-PARSE-03
"""
import pytest
from generate_release_notes import GherkinParser

FEATURE_CONTENT = """\
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


@pytest.fixture
def parsed(tmp_path):
    (tmp_path / "auth.feature").write_text(FEATURE_CONTENT)
    return GherkinParser().parse_dir(tmp_path)


def test_parser_extracts_scenario_names(parsed):
    """REQ-PARSE-01: Scenario names are extracted from a feature file."""
    names = [s["name"] for s in parsed[0]["scenarios"]]
    assert "User registers with valid credentials" in names
    assert "User logs in" in names


def test_parser_extracts_req_tags(parsed):
    """REQ-PARSE-02: @req-* and @FR-* tags are associated with scenarios."""
    all_req_tags = [t for s in parsed[0]["scenarios"] for t in s["req_tags"]]
    assert "req-AUTH-01" in all_req_tags
    assert "FR-AUTH-02" in all_req_tags


def test_parser_story_tags_not_in_req_tags(parsed):
    """REQ-PARSE-02: @story-* tags are NOT included in req_tags."""
    all_req_tags = [t for s in parsed[0]["scenarios"] for t in s["req_tags"]]
    assert not any(t.startswith("story-") for t in all_req_tags)


def test_parser_extracts_steps(parsed):
    """REQ-PARSE-03: Given/When/Then steps are extracted for each scenario."""
    first = parsed[0]["scenarios"][0]
    keywords = [s["keyword"] for s in first["steps"]]
    assert "Given" in keywords
    assert "When" in keywords
    assert "Then" in keywords


def test_parser_handles_empty_directory(tmp_path):
    """REQ-PARSE-01: Parsing an empty directory returns an empty list."""
    result = GherkinParser().parse_dir(tmp_path)
    assert result == []


def test_parser_extracts_feature_name(parsed):
    """REQ-PARSE-01: The Feature: header is captured."""
    assert parsed[0]["feature"] == "User authentication"
