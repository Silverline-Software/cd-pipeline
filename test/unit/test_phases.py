# test/unit/test_phases.py
"""Unit tests for the locked Phase enum.

Requirements covered: REQ-PHASE-01, REQ-PHASE-02, REQ-PHASE-03
"""
import pytest

from silverline.reporting.phases import Phase


def test_phase_values_are_locked_and_ordered():
    """REQ-PHASE-01: MVP is 0 and phases sort ascending by integer value."""
    assert Phase.MVP.value == 0
    assert Phase.PHASE_10.value == 10
    ordered = sorted(Phase)
    assert ordered[0] is Phase.MVP
    assert ordered[-1] is Phase.PHASE_10


def test_phase_label():
    """REQ-PHASE-02: label renders 'MVP' for 0 and 'Phase N' otherwise."""
    assert Phase.MVP.label == "MVP"
    assert Phase.PHASE_1.label == "Phase 1"
    assert Phase.PHASE_10.label == "Phase 10"


@pytest.mark.parametrize("text,expected", [
    ("MVP", Phase.MVP),
    ("mvp", Phase.MVP),
    ("Phase 2", Phase.PHASE_2),
    ("phase-2", Phase.PHASE_2),
    ("2", Phase.PHASE_2),
    ("", Phase.MVP),
    ("nonsense", Phase.MVP),
])
def test_phase_parse(text, expected):
    """REQ-PHASE-03: parse normalizes common spellings, defaults to MVP."""
    assert Phase.parse(text) is expected


@pytest.mark.parametrize("value,expected", [
    (Phase.PHASE_2, Phase.PHASE_2),   # Phase passthrough
    (2, Phase.PHASE_2),               # int input
    (0, Phase.MVP),
    (10, Phase.PHASE_10),
    (25, Phase.MVP),                  # out-of-range int → MVP
    (11, Phase.MVP),
    (True, Phase.MVP),                # bool guarded → MVP
    (False, Phase.MVP),
    (None, Phase.MVP),
])
def test_phase_parse_non_string_inputs(value, expected):
    """REQ-PHASE-03: parse handles Phase/int/bool/None, out-of-range → MVP."""
    assert Phase.parse(value) is expected


@pytest.mark.parametrize("text,expected", [
    ("v2", Phase.MVP),         # version string, not a phase
    ("3.7", Phase.MVP),        # decimal → MVP
    ("-3", Phase.MVP),         # negative → MVP
    ("Phase 25", Phase.MVP),   # out-of-range → MVP
    ("phase_2", Phase.PHASE_2),
    ("phase2", Phase.PHASE_2),
])
def test_phase_parse_rejects_garbage(text, expected):
    """REQ-PHASE-03: only well-formed phase spellings parse; junk → MVP."""
    assert Phase.parse(text) is expected
