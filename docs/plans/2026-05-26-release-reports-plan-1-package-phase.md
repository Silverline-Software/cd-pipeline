# Release Reports — Plan 1: Package + Phase Enum + Per-Requirement Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the report generator a pip-installable package (installable from a git tag) and replace category-level phase with a locked per-requirement `Phase` enum, so reports group `Phase → Category → Requirement` using each requirement's own phase.

**Architecture:** Move the two standalone scripts into a `silverline.reporting` subpackage as the source of truth; keep `scripts/*.py` as thin re-export shims so existing imports, tests, and Makefile targets keep working. Add a locked `Phase(IntEnum)` (MVP=0 … PHASE_10=10) and a manifest loader that normalizes legacy 3-tuple and new 4-tuple requirement entries into `Requirement` dataclasses. Retarget the existing HTML phase-block loop from category-phase to requirement-phase.

**Tech Stack:** Python 3.11, `enum.IntEnum`, `dataclasses`, setuptools/`pyproject.toml`, pytest + pytest-bdd.

**Reference spec:** `docs/plans/2026-05-26-release-reports-package-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` (create) | Package metadata; declare `silverline*` packages; console entrypoint `silverline-release-notes` |
| `silverline/reporting/__init__.py` (create) | Re-export `Phase`, `Requirement`, `load_manifest`, `ReportBuilder`, schema symbols |
| `silverline/reporting/phases.py` (create) | Locked `Phase` IntEnum + `label` + `parse` |
| `silverline/reporting/manifest.py` (create) | `Requirement` dataclass + `load_manifest()` (CWD discovery, sys.modules preload, legacy/new normalization) |
| `silverline/reporting/schema.py` (create) | Verbatim contents of `scripts/release_notes_schema.py` + `phase` added to requirement object docs |
| `silverline/reporting/generate.py` (create) | Verbatim contents of `scripts/generate_release_notes.py` with manifest-load + phase-grouping retargeted (see Tasks 5–6) |
| `scripts/release_notes_schema.py` (modify) | Thin shim: `from silverline.reporting.schema import *` |
| `scripts/generate_release_notes.py` (modify) | Thin shim: `from silverline.reporting.generate import *` + `__main__` calls `main()` |
| `examples/requirements_manifest.py` (modify) | Add per-requirement `Phase` to entries; import `Phase` |
| `scripts/requirements_manifest.py` (modify) | Add per-requirement `Phase` to this repo's own manifest |
| `test/unit/test_phases.py` (create) | Phase ordering/label/parse |
| `test/unit/test_manifest_loader.py` (create) | Legacy 3-tuple + new 4-tuple normalization |
| `test/unit/test_report_builder.py` (modify) | Assert phase grouping + phase in JSON |
| `pytest.ini` (modify) | Register new markers |

---

## Task 1: Create the `Phase` enum

**Files:**
- Create: `silverline/reporting/__init__.py`
- Create: `silverline/reporting/phases.py`
- Test: `test/unit/test_phases.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest test/unit/test_phases.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'silverline.reporting'`

- [ ] **Step 3: Create the package marker and enum**

```python
# silverline/reporting/__init__.py
"""
file: silverline/reporting/__init__.py
author: Stephen Boyett

description:
    Public surface of the release-reporting package: the locked Phase enum,
    the Requirement dataclass + manifest loader, the report builder, and the
    JSON schema helpers. Imported by the console entrypoints and the thin
    scripts/ shims.

---
Copyright © 2026 Silverline Software LLC. All Rights Reserved.
---
"""
from silverline.reporting.phases import Phase  # noqa: F401
```

```python
# silverline/reporting/phases.py
"""
file: silverline/reporting/phases.py
author: Stephen Boyett

description:
    The locked, ordered implementation-phase enumeration. MVP is 0; phases
    sort ascending by integer value so ordering is identical across every
    Silverline project. Reports group requirements by these phases.

---
Copyright © 2026 Silverline Software LLC. All Rights Reserved.
---
"""
from __future__ import annotations

import re
from enum import IntEnum


class Phase(IntEnum):
    """Locked implementation phases. Do not renumber existing members."""

    MVP = 0
    PHASE_1 = 1
    PHASE_2 = 2
    PHASE_3 = 3
    PHASE_4 = 4
    PHASE_5 = 5
    PHASE_6 = 6
    PHASE_7 = 7
    PHASE_8 = 8
    PHASE_9 = 9
    PHASE_10 = 10

    @property
    def label(self) -> str:
        """Human-readable label: 'MVP' for 0, else 'Phase N'."""
        return "MVP" if self is Phase.MVP else f"Phase {self.value}"

    @classmethod
    def parse(cls, text: object) -> "Phase":
        """Coerce a string/int/Phase to a Phase. Unknown/empty → MVP.

        Accepts 'MVP', 'Phase 2', 'phase-2', '2', 2, Phase.PHASE_2.
        """
        if isinstance(text, Phase):
            return text
        if isinstance(text, int):
            return cls(text) if text in cls._value2member_map_ else cls.MVP
        s = str(text or "").strip().lower()
        if not s or s == "mvp":
            return cls.MVP
        m = re.search(r"(\d+)", s)
        if m:
            n = int(m.group(1))
            if n in cls._value2member_map_:
                return cls(n)
        return cls.MVP
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest test/unit/test_phases.py -v`
Expected: PASS (6+ cases)

- [ ] **Step 5: Commit**

```bash
git add silverline/reporting/__init__.py silverline/reporting/phases.py test/unit/test_phases.py
git commit -m "feat(reporting): add locked Phase enum (MVP=0..PHASE_10)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Add `Requirement` dataclass + manifest loader

The current generator loads the manifest at module import via an `importlib` CWD search (`generate.py` lines 43–61). Extract that into a reusable, testable `load_manifest()` that also checks `sys.modules` first (so the test conftest preload is honored) and normalizes requirement entries into `Requirement` dataclasses with a resolved `Phase`.

**Files:**
- Create: `silverline/reporting/manifest.py`
- Test: `test/unit/test_manifest_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# test/unit/test_manifest_loader.py
"""Unit tests for manifest normalization.

Requirements covered: REQ-MANIFEST-01, REQ-MANIFEST-02
"""
import types

from silverline.reporting.manifest import Requirement, normalize_requirements
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest test/unit/test_manifest_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'silverline.reporting.manifest'`

- [ ] **Step 3: Implement the loader**

```python
# silverline/reporting/manifest.py
"""
file: silverline/reporting/manifest.py
author: Stephen Boyett

description:
    Loads a project's requirements_manifest.py and normalizes its REQUIREMENTS
    table into Requirement dataclasses with a resolved Phase. Supports the
    legacy 3-tuple form (phase inherited from the requirement's category) and
    the new 4-tuple form (explicit per-requirement Phase). The manifest is
    project-specific and lives in the caller's repo, never in this package.

See Also:
    silverline/reporting/phases.py
    examples/requirements_manifest.py

---
Copyright © 2026 Silverline Software LLC. All Rights Reserved.
---
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from silverline.reporting.phases import Phase


@dataclass(frozen=True)
class Requirement:
    id: str
    description: str
    priority: str
    status: str
    phase: Phase
    category: str


def _category_phase(mod: object, category: str) -> Phase:
    """Resolve a category's phase (legacy category-level 'phase' key)."""
    cats = getattr(mod, "CATEGORIES", {}) or {}
    cat = cats.get(category, {})
    return Phase.parse(cat.get("phase", 0))


def normalize_requirements(mod: object) -> dict[str, Requirement]:
    """Normalize a manifest module's REQUIREMENTS into Requirement objects."""
    raw = getattr(mod, "REQUIREMENTS", {}) or {}
    out: dict[str, Requirement] = {}
    for req_id, entry in raw.items():
        category = req_id.split("-")[0]
        desc, priority, status = entry[0], entry[1], entry[2]
        if len(entry) >= 4:
            phase = Phase.parse(entry[3])
        else:
            phase = _category_phase(mod, category)
        out[req_id] = Requirement(
            id=req_id, description=desc, priority=priority,
            status=status, phase=phase, category=category,
        )
    return out


def load_manifest_module() -> ModuleType | None:
    """Find and import the caller's requirements_manifest.

    Order: an already-imported module in sys.modules (test preload), then
    CWD/scripts/requirements_manifest.py, then CWD/requirements_manifest.py.
    Returns None if no manifest is found.
    """
    if "requirements_manifest" in sys.modules:
        return sys.modules["requirements_manifest"]
    for rdir in (Path.cwd() / "scripts", Path.cwd()):
        mpath = rdir / "requirements_manifest.py"
        if mpath.exists():
            spec = importlib.util.spec_from_file_location("requirements_manifest", mpath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules["requirements_manifest"] = mod
            return mod
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest test/unit/test_manifest_loader.py -v`
Expected: PASS (2 cases)

- [ ] **Step 5: Export from package init and commit**

Add to `silverline/reporting/__init__.py`:
```python
from silverline.reporting.manifest import Requirement, normalize_requirements, load_manifest_module  # noqa: F401
```

```bash
git add silverline/reporting/manifest.py silverline/reporting/__init__.py test/unit/test_manifest_loader.py
git commit -m "feat(reporting): add Requirement dataclass + phase-aware manifest loader

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Move schema into the package behind a shim

**Files:**
- Create: `silverline/reporting/schema.py`
- Modify: `scripts/release_notes_schema.py`

- [ ] **Step 1: Create the package module with the existing schema content**

Copy the **entire current contents** of `scripts/release_notes_schema.py` (109 lines, unchanged) into `silverline/reporting/schema.py`. Then extend the requirement-object documentation: in `EXECUTIVE_REPORT_SCHEMA`, the `requirements` value stays `list` (the validator only checks list presence), but add a module-level comment above it documenting the per-requirement object shape now includes `"phase": str` (the phase label). No validator change is required because nested list items aren't type-checked.

- [ ] **Step 2: Replace the script with a thin shim**

```python
# scripts/release_notes_schema.py
"""Thin shim — schema now lives in silverline.reporting.schema.

Kept so existing imports (`from release_notes_schema import ...`) and the
test suite continue to work after packaging.
"""
from silverline.reporting.schema import *  # noqa: F401,F403
from silverline.reporting.schema import (  # noqa: F401
    COVERAGE_SUMMARY_SCHEMA,
    EXECUTIVE_REPORT_SCHEMA,
    UNIT_TEST_SUMMARY_SCHEMA,
    validate_report,
)
```

- [ ] **Step 3: Run schema tests to verify they still pass**

Run: `python3 -m pytest test/unit/test_schema.py -v`
Expected: PASS (all existing REQ-SCHEMA cases)

- [ ] **Step 4: Commit**

```bash
git add silverline/reporting/schema.py scripts/release_notes_schema.py
git commit -m "refactor(reporting): move schema into package, leave shim

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Move the generator into the package behind a shim (no logic change yet)

This task is a pure move so the diff in Tasks 5–6 is small and reviewable.

**Files:**
- Create: `silverline/reporting/generate.py`
- Modify: `scripts/generate_release_notes.py`

- [ ] **Step 1: Copy generator into the package**

Copy the **entire current contents** of `scripts/generate_release_notes.py` into `silverline/reporting/generate.py` verbatim. Then change only the import block:
- Replace `sys.path.insert(0, str(Path(__file__).parent))` + `from release_notes_schema import (...)` (lines 34–40) with `from silverline.reporting.schema import (COVERAGE_SUMMARY_SCHEMA, EXECUTIVE_REPORT_SCHEMA, UNIT_TEST_SUMMARY_SCHEMA, validate_report)`.
- Leave the module-level `CATEGORIES/PHASES/REQUIREMENTS/normalize_tag` import block (lines 43–61) **unchanged for now** — Task 5 replaces it.

- [ ] **Step 2: Replace the script with a thin shim**

```python
# scripts/generate_release_notes.py
"""Thin shim — generator now lives in silverline.reporting.generate.

Kept so `from generate_release_notes import ReportBuilder`, the CLI
subprocess tests, and the Makefile `generate` targets keep working.
"""
import sys

from silverline.reporting.generate import *  # noqa: F401,F403
from silverline.reporting.generate import ReportBuilder, main  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the full unit suite**

Run: `python3 -m pytest test/unit/ -v`
Expected: PASS — `from generate_release_notes import ReportBuilder` resolves via the shim; CLI subprocess tests still pass (they invoke `scripts/generate_release_notes.py`, which now delegates to the package).

> If `silverline` is not importable in the subprocess (CLI tests run `scripts/generate_release_notes.py` directly), confirm the package is importable from repo root. It is, because repo root is on `sys.path` for the subprocess CWD. If not, Task 8's editable install resolves it; run Task 8 before re-checking these two CLI tests.

- [ ] **Step 4: Commit**

```bash
git add silverline/reporting/generate.py scripts/generate_release_notes.py
git commit -m "refactor(reporting): move generator into package, leave shim

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Wire the generator to the new manifest loader

**Files:**
- Modify: `silverline/reporting/generate.py` (the module-level manifest block, formerly lines 43–61)

- [ ] **Step 1: Replace the importlib block with the loader + normalized requirements**

Replace the entire `import importlib.util as _ilu` … `def normalize_tag(t): return t` block with:

```python
from silverline.reporting.manifest import load_manifest_module, normalize_requirements
from silverline.reporting.phases import Phase

_manifest_mod = load_manifest_module()
if _manifest_mod is not None:
    CATEGORIES = getattr(_manifest_mod, "CATEGORIES", {})
    PHASES = getattr(_manifest_mod, "PHASES", {})
    REQUIREMENTS = getattr(_manifest_mod, "REQUIREMENTS", {})
    normalize_tag = getattr(_manifest_mod, "normalize_tag", lambda t: t)
else:
    CATEGORIES, PHASES, REQUIREMENTS = {}, {}, {}
    def normalize_tag(t):  # noqa: E731
        return t

# Normalized Requirement objects keyed by id (phase resolved per-requirement)
NORM_REQUIREMENTS = normalize_requirements(_manifest_mod) if _manifest_mod else {}
```

- [ ] **Step 2: Run the unit suite to verify no regression**

Run: `python3 -m pytest test/unit/ -v`
Expected: PASS (existing behavior unchanged; `NORM_REQUIREMENTS` not yet consumed)

- [ ] **Step 3: Commit**

```bash
git add silverline/reporting/generate.py
git commit -m "refactor(reporting): load manifest via normalized loader

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Retarget HTML grouping to per-requirement phase

Replace the outer phase loop (current `generate.py` block corresponding to old lines 1187–1343) so it groups by each requirement's own `Phase`, then by category, rendering only non-empty phases in ascending enum order. The requirement-row rendering inside (status symbol, scenarios, badges) is reused unchanged; only the iteration changes, plus the unpacking now reads the normalized `Requirement`.

**Files:**
- Modify: `silverline/reporting/generate.py`
- Test: `test/unit/test_report_builder.py`

- [ ] **Step 1: Write the failing test**

```python
# Append to test/unit/test_report_builder.py
from silverline.reporting.phases import Phase


def test_html_groups_requirements_by_phase(tmp_path, monkeypatch):
    """REQ-PHASE-04: HTML renders phase sections in ascending order, MVP first."""
    import generate_release_notes as g
    from silverline.reporting.manifest import Requirement

    monkeypatch.setattr(g, "CATEGORIES", {
        "AUTH": {"name": "Auth", "description": "d", "phase": 0, "order": 1},
    })
    monkeypatch.setattr(g, "REQUIREMENTS", {
        "AUTH-01": ("MVP req", "P0", "Implemented", Phase.MVP),
        "AUTH-09": ("Later req", "P1", "Planned", Phase.PHASE_2),
    })
    html = make_builder().build_executive_html(
        report=make_builder().build_executive_report(None, None, None),
        features=None,
    )
    assert "MVP" in html and "Phase 2" in html
    assert html.index("MVP") < html.index("Phase 2")
    assert "AUTH-01" in html and "AUTH-09" in html
```

> Note: confirm the exact `build_executive_html` signature in `generate.py` and adjust the call to match. If it takes assembled fragments rather than `(report, features)`, construct via the same path `main()` uses. The assertion targets — ascending phase order and both req ids present — stay the same.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest test/unit/test_report_builder.py::test_html_groups_requirements_by_phase -v`
Expected: FAIL — `Phase 2` not present (old loop groups by category-phase=0 only) or ordering wrong.

- [ ] **Step 3: Replace the phase loop**

Replace the `for phase_num in sorted(PHASES.keys()):` block (down to the closing `</div>` append for `phase-block`) with iteration over the `Phase` enum, selecting normalized requirements per phase:

```python
# ── Requirement hierarchy: Phase → Category → Requirement → Scenario ──
req_html = ""
total_reqs = 0
total_tested = 0

# Group normalized requirements by phase, then category (preserving category order)
norm = NORM_REQUIREMENTS
cat_order = {k: v.get("order", 0) for k, v in CATEGORIES.items()}

for phase in sorted(Phase):
    phase_reqs = {rid: r for rid, r in norm.items() if r.phase is phase}
    if not phase_reqs:
        continue

    # categories present in this phase, in declared order
    cats_in_phase = sorted(
        {r.category for r in phase_reqs.values()},
        key=lambda c: cat_order.get(c, 999),
    )

    phase_content = ""
    for cat_key in cats_in_phase:
        cat = CATEGORIES.get(cat_key, {"name": cat_key, "description": ""})
        cat_reqs = sorted(
            [(rid, r) for rid, r in phase_reqs.items() if r.category == cat_key],
            key=lambda x: x[0],
        )
        cat_passing = 0
        cat_total = len(cat_reqs)
        total_reqs += cat_total
        req_items_html = ""

        for req_id, req in cat_reqs:
            desc, priority, impl_status = req.description, req.priority, req.status
            scenarios = req_scenarios.get(req_id, [])
            # ── (reuse the EXISTING per-requirement rendering block verbatim:
            #     test_st computation, scenarios_html, check_sym, impl_cls,
            #     sc_label, req_items_html += <details ...>) ──

        phase_content += (
            # ── (reuse the EXISTING category-section <details> append verbatim) ──
        )

    # Phase heading: label from the enum; optional description from PHASES if present
    phase_desc = ""
    if isinstance(PHASES, dict):
        pmeta = PHASES.get(phase.value) or PHASES.get(phase)
        if isinstance(pmeta, dict):
            phase_desc = pmeta.get("description", "")
    req_html += (
        f'<div class="phase-block">'
        f'<h3 class="phase-heading">{esc(phase.label)}</h3>'
        + (f'<p class="phase-desc">{esc(phase_desc)}</p>' if phase_desc else "")
        + f'{phase_content}'
        f'</div>\n'
    )
```

The two `# ── (reuse … verbatim)` blocks are the **exact** existing inner-rendering lines (the `for req_id, (desc, priority, impl_status) in cat_reqs:` body and the `phase_content += (<details class="category-section" open> …)` append). Keep them character-for-character; only their surrounding loop changed. The `for` body's tuple-unpack line is dropped because `desc/priority/impl_status` are now read from `req` above.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest test/unit/test_report_builder.py -v`
Expected: PASS — including the new phase-ordering test and all existing GEN cases.

- [ ] **Step 5: Add `phase` to each requirement object in the JSON report**

In `_build_requirements` (current lines 940–947), enrich each emitted requirement dict with its manifest phase label so the JSON carries phase too:

```python
requirements.append(
    {
        "requirement_id": req_id,
        "status": req_status,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "phase": NORM_REQUIREMENTS[req_id].phase.label
                 if req_id in NORM_REQUIREMENTS else Phase.MVP.label,
    }
)
```

- [ ] **Step 6: Run full unit suite + commit**

Run: `python3 -m pytest test/unit/ -v`
Expected: PASS

```bash
git add silverline/reporting/generate.py test/unit/test_report_builder.py
git commit -m "feat(reporting): group report by per-requirement Phase, add phase to JSON

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Update example + own manifests to the new schema

**Files:**
- Modify: `examples/requirements_manifest.py`
- Modify: `scripts/requirements_manifest.py`

- [ ] **Step 1: Update the example manifest to per-requirement phase**

In `examples/requirements_manifest.py`: import the enum and add an explicit `Phase` as the 4th tuple element on each requirement. Update the header comment from "(description, priority, status)" to "(description, priority, status, phase)".

```python
from silverline.reporting.phases import Phase

REQUIREMENTS = {
    "AUTH-01": ("User can register with email and password", "P0", "Implemented", Phase.MVP),
    "AUTH-02": ("User can log in with valid credentials", "P0", "Implemented", Phase.MVP),
    "AUTH-03": ("User can log out", "P0", "Implemented", Phase.MVP),
    "AUTH-04": ("Password reset via email link", "P0", "Planned", Phase.PHASE_1),
    "DASH-01": ("View account information", "P0", "Implemented", Phase.MVP),
    "DASH-02": ("Edit profile settings", "P1", "Planned", Phase.PHASE_2),
    "ADMIN-01": ("Admin can view all users", "P0", "Implemented", Phase.MVP),
    "ADMIN-02": ("Admin can disable accounts", "P0", "Planned", Phase.PHASE_2),
}
```

Keep the legacy `CATEGORIES[...]["phase"]` keys in place — the loader ignores them when an explicit per-requirement phase is present, and they document backward compatibility.

- [ ] **Step 2: Update this repo's own manifest the same way**

Apply the same 4th-element `Phase` addition to each entry in `scripts/requirements_manifest.py` (this repo's GEN/SCHEMA/PARSE/etc. requirements). Set everything implemented today to `Phase.MVP`.

- [ ] **Step 3: Smoke-generate and eyeball the HTML**

Run: `make generate-example && python3 -c "import pathlib;print('phase-block' in pathlib.Path('release/executive-report.html').read_text())"`
Expected: prints `True`; open `release/executive-report.html` and confirm MVP renders before later phases.

- [ ] **Step 4: Commit**

```bash
git add examples/requirements_manifest.py scripts/requirements_manifest.py
git commit -m "feat(manifest): adopt per-requirement Phase in example + own manifest

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Add `pyproject.toml` packaging + console entrypoint

**Files:**
- Create: `pyproject.toml`
- Create: `examples/README.md` (sibling metadata for the YAML/JSON-free dir, per file-header standard)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "silverline-cd-pipeline"
version = "1.0.0"
description = "Silverline release-report generator and CD pipeline toolkit."
requires-python = ">=3.11"
authors = [{ name = "Stephen Boyett" }]
dependencies = []

[project.optional-dependencies]
test = ["pytest", "pytest-bdd"]

[project.scripts]
silverline-release-notes = "silverline.reporting.generate:main"

[tool.setuptools.packages.find]
include = ["silverline*"]
```

- [ ] **Step 2: Editable install and verify the entrypoint**

Run:
```bash
pip install -e .
silverline-release-notes --output-dir /tmp/sr --owner o --repo r --release-tag t-v0.0.1 --commit abc
```
Expected: exit 0; `/tmp/sr/executive-report.html` and `.json` exist. (Run from a dir where a `requirements_manifest.py` is discoverable, or with `PYTHONPATH=examples`.)

- [ ] **Step 3: Run the entire suite**

Run: `python3 -m pytest test/ -v`
Expected: PASS — unit + acceptance. Confirm the two CLI subprocess tests in `test_report_builder.py` pass now that `silverline` is installed/importable.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml examples/README.md
git commit -m "build: package silverline-cd-pipeline with release-notes entrypoint

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Register markers, update docs, tag v1.0.0

**Files:**
- Modify: `pytest.ini`
- Modify: `README.md`, `CLAUDE.md`

- [ ] **Step 1: Register new markers in `pytest.ini`**

Add under `markers =`:
```
    req-PHASE-01: Phase enum values are locked and ordered
    req-PHASE-02: Phase label renders MVP / Phase N
    req-PHASE-03: Phase.parse normalizes spellings
    req-PHASE-04: HTML groups requirements by per-requirement phase
    req-MANIFEST-01: legacy 3-tuple requirement inherits category phase
    req-MANIFEST-02: new 4-tuple requirement uses explicit phase
```

- [ ] **Step 2: Document the new install path + phase field**

In `README.md`: add an "Install as a package (recommended)" subsection showing `pip install "git+https://github.com/Silverline-Software/cd-pipeline@v1.0.0"` and `silverline-release-notes …`; update the manifest section to document the 4th `Phase` tuple element. In `CLAUDE.md`: note `silverline/reporting/` is the generator's source of truth and `scripts/*.py` are shims.

- [ ] **Step 3: Full check + commit + tag**

Run: `make check && python3 -m pytest test/ -v`
Expected: PASS

```bash
git add pytest.ini README.md CLAUDE.md
git commit -m "docs: package install path + per-requirement Phase; register markers

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git tag v1.0.0
git push origin main --tags
```

---

## Self-Review (completed)

- **Spec coverage:** Package + git-tag install → Tasks 3,4,8,9. Phase enum → Task 1. Per-requirement phase schema + backward compat → Tasks 2,7. Phase→Category→Requirement layout → Task 6. JSON gains phase → Task 6 Step 5. (BMAD generator, workflow updates, and the skill are Plans 2 & 3 — see roadmap.)
- **Placeholder scan:** The two `# ── (reuse … verbatim)` markers in Task 6 reference the *existing* code blocks explicitly (with their identifying first lines) rather than inventing new code — this is a deliberate "move verbatim" instruction, not a TODO.
- **Type consistency:** `Phase`, `Requirement(id, description, priority, status, phase, category)`, `normalize_requirements`, `load_manifest_module`, `NORM_REQUIREMENTS` are used consistently across Tasks 2/5/6/7.

---

## Roadmap — Plans 2 & 3 (separate plans, written after Plan 1 lands)

**Plan 2 — `silverline-manifest-from-bmad`:** parse `_bmad-output/planning-artifacts/**/PRD.md` (FR id, description, priority, explicit `[Phase N]` marker → `Phase.parse`), `requirement-traceability-matrix.md` (FR→story links), and `sprint-status.yaml` (story state → Implemented/Planned/Backlog). Emit a generated `scripts/requirements_manifest.py` using the Task-2 schema. Add console entrypoint `silverline-manifest-from-bmad`. TDD against a fixture `_bmad-output/` tree.

**Plan 3 — workflows + skill:** update `silverline-ci-reusable.yml` to `pip install` the pinned tag and call the entrypoints (new `pipeline-ref` + `bmad` inputs); author the `silverline-release-reports-setup` skill (detect BMAD, wire CI/CD, generate manifest, verify FR tags, confirm Firebase env, local smoke-generate), referencing the README + phase-aware HTML template.
