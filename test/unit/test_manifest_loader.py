# test/unit/test_manifest_loader.py
"""Unit tests for manifest normalization.

Requirements covered: REQ-MANIFEST-01, REQ-MANIFEST-02, REQ-MANIFEST-03
"""
import sys
import types

import pytest

from silverline.reporting.manifest import Requirement, normalize_requirements, load_manifest_module
from silverline.reporting.phases import Phase


def _module(**attrs):
    m = types.SimpleNamespace()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def test_legacy_3tuple_uses_category_phase():
    """REQ-MANIFEST-01: a 3-tuple entry inherits phase from its category."""
    mod = _module(
        CATEGORIES={"AUTH": {"name": "Auth", "description": "", "phase": 1, "order": 1}},
        PHASES={1: {"name": "Phase 1", "description": ""}},
        REQUIREMENTS={"AUTH-01": ("Register", "P0", "Implemented")},
    )
    reqs = normalize_requirements(mod)
    assert reqs["AUTH-01"] == Requirement(
        id="AUTH-01", description="Register", priority="P0",
        status="Implemented", phase=Phase.PHASE_1, category="AUTH",
    )


def test_new_4tuple_uses_explicit_phase():
    """REQ-MANIFEST-02: a 4-tuple entry uses its explicit Phase, overriding category."""
    mod = _module(
        CATEGORIES={"AUTH": {"name": "Auth", "description": "", "phase": 1, "order": 1}},
        PHASES={},
        REQUIREMENTS={"AUTH-04": ("Reset", "P0", "Planned", Phase.PHASE_2)},
    )
    reqs = normalize_requirements(mod)
    assert reqs["AUTH-04"].phase is Phase.PHASE_2
    assert reqs["AUTH-04"].category == "AUTH"


@pytest.fixture
def _clean_manifest_module():
    """Remove any preloaded requirements_manifest from sys.modules, restore after."""
    saved = sys.modules.pop("requirements_manifest", None)
    try:
        yield
    finally:
        sys.modules.pop("requirements_manifest", None)
        if saved is not None:
            sys.modules["requirements_manifest"] = saved


def test_load_returns_none_when_no_manifest(_clean_manifest_module, monkeypatch, tmp_path):
    """REQ-MANIFEST-03: returns None when no requirements_manifest.py exists."""
    monkeypatch.chdir(tmp_path)
    assert load_manifest_module() is None


def test_load_finds_manifest_in_scripts(_clean_manifest_module, monkeypatch, tmp_path):
    """REQ-MANIFEST-03: discovers and imports CWD/scripts/requirements_manifest.py."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "requirements_manifest.py").write_text(
        "REQUIREMENTS = {'X-01': ('d', 'P0', 'Implemented')}\n"
        "CATEGORIES = {}\nPHASES = {}\n"
    )
    monkeypatch.chdir(tmp_path)
    mod = load_manifest_module()
    assert mod is not None
    assert mod.REQUIREMENTS == {"X-01": ("d", "P0", "Implemented")}


def test_load_honors_preloaded_sys_modules(_clean_manifest_module, monkeypatch, tmp_path):
    """REQ-MANIFEST-03: a module already in sys.modules wins over filesystem search."""
    sentinel = types.ModuleType("requirements_manifest")
    sentinel.REQUIREMENTS = {"SENTINEL-01": ("s", "P0", "Implemented")}
    sys.modules["requirements_manifest"] = sentinel
    monkeypatch.chdir(tmp_path)  # no manifest on disk; cache must win
    assert load_manifest_module() is sentinel
