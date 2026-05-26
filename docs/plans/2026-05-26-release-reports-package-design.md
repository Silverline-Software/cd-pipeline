# Release Reports as a Versioned Package + BMAD Auto-Manifest — Design

**Status:** Approved design — pending implementation plan
**Author:** Stephen Boyett
**Date:** 2026-05-26

**Goal:** Make `release/executive-report.html` generation trivially reusable across every Silverline client repo, with Functional Requirements mapped into the report automatically from each project's BMAD artifacts — without copying generator code into each repo. Add a locked, ordered **Phase** dimension so reports group requirements by implementation phase (MVP → Phase 1 → … → Phase 10). Ship a reusable Claude skill that wires any repo in.

---

## Problem

Today the generator (`scripts/generate_release_notes.py`, `scripts/release_notes_schema.py`) is **copied** into every consumer repo. The "reusable" CI workflow (`silverline-ci-reusable.yml`) still runs `python scripts/generate_release_notes.py` against the *caller's* checkout, so it too depends on the copied script. Consequences:

- Generator improvements never propagate — every repo drifts to whatever version it copied.
- Each consumer hand-maintains `requirements_manifest.py`, duplicating the FR data already in its BMAD PRD / RTM / sprint-status.
- Phase is only expressible at the **category** level (`CATEGORIES[...]["phase"]`), so requirements in one category cannot span phases.

## Decisions (resolved during brainstorming)

| Fork | Decision |
|---|---|
| How generator code reaches repos | **pip package**, installed **from git tag** (`pip install "git+https://github.com/Silverline-Software/cd-pipeline@v1.0.0"`) — no PyPI publishing, version-pinned, private-repo friendly |
| FR source of truth | **Auto-generate** `requirements_manifest.py` **from BMAD artifacts** |
| FR status (Implemented/Planned/Backlog) | **Derive from `sprint-status.yaml`** via RTM FR→story links |
| Phase model | **Locked `IntEnum`**, `MVP=0` … `PHASE_10=10`; deterministic ascending order; only non-empty phases render |
| FR → Phase mapping | **Explicit phase marker per FR in the PRD** (e.g. `FR-012 [Phase 2] — …`), default `MVP` when absent |
| Report layout | **Phase (top) → Category → Requirement** |
| Handoff artifact | A reusable **Claude skill** (`silverline-release-reports-setup`) |

---

## Architecture

### 1. Package the generator (`silverline/reporting/`)

Move the standalone scripts into the existing `silverline` package and expose console entrypoints via `pyproject.toml`. cd-pipeline becomes pip-installable; consumer repos pin a tag.

```
silverline/
  reporting/
    __init__.py
    phases.py        # locked Phase IntEnum (new)
    schema.py        # from scripts/release_notes_schema.py
    manifest.py      # Requirement dataclass + manifest loader (phase-aware)
    generate.py      # from scripts/generate_release_notes.py (report builder + HTML)
    bmad.py          # BMAD PRD/RTM/sprint-status parser → manifest emitter (new)
```

`pyproject.toml` `[project.scripts]`:

| Entrypoint | Purpose |
|---|---|
| `silverline-release-notes` | Generate JSON + HTML report (current CLI, unchanged flags) |
| `silverline-manifest-from-bmad` | Emit `requirements_manifest.py` from BMAD artifacts |

**Backward compatibility:** `scripts/generate_release_notes.py` and `scripts/release_notes_schema.py` remain as **thin shims** that import from `silverline.reporting`, so existing callers, tests, and the current Makefile targets keep working during migration.

### 2. Locked Phase enum (`silverline/reporting/phases.py`)

```python
from enum import IntEnum

class Phase(IntEnum):
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
        return "MVP" if self is Phase.MVP else f"Phase {self.value}"

    @classmethod
    def parse(cls, text: str) -> "Phase":
        """Parse 'MVP', 'Phase 2', 'phase-2', '2', etc. → Phase. Defaults to MVP."""
```

- Ordering is by integer value → MVP always first; cannot drift between projects.
- Only phases that contain at least one requirement render in a report.

### 3. Requirement schema gains `phase`

`requirements_manifest.py` `REQUIREMENTS` entries accept an optional 4th element. The loader normalizes every entry into a `Requirement` dataclass:

```python
@dataclass(frozen=True)
class Requirement:
    id: str            # "AUTH-01"
    description: str
    priority: str      # P0 | P1 | P2
    status: str        # Implemented | Planned | Backlog
    phase: Phase
    category: str      # "AUTH"
```

Loader accepts both forms for backward compatibility:
- **legacy** `("desc", "P0", "Implemented")` → `phase` inferred from the category's old `phase` key, mapped onto the enum (`1 → Phase.PHASE_1`, missing → `Phase.MVP`).
- **new** `("desc", "P0", "Implemented", Phase.PHASE_2)` → explicit per-requirement phase.

`PHASES` dict (today free-form integers) is retained only for optional per-phase display description; phase **ordering and labels come from the enum**, not from `PHASES`.

### 4. Report layout — Phase → Category → Requirement

The HTML report renders top-level sections in ascending `Phase` order. Within each phase, requirements group by category (existing category sub-section rendering), each requirement showing its status indicator (✓ / ✗ / ~ / —) and expandable Gherkin scenarios. A phase section is omitted entirely if it has no requirements.

```
MVP
  Authentication
    ✓ AUTH-01  Register with email
    ✓ AUTH-02  Log in
  Dashboard
    ✓ DASH-01  View account
Phase 2
  Authentication
    ~ AUTH-04  Password reset
  Dashboard
    — DASH-02  Edit profile
```

The HTML template (current dark Silverline brand styling in `executive-report.html`) gains a phase-section wrapper with a phase header band; category sub-headers nest beneath. Per-phase pass/fail rollup counts are shown in each phase header.

### 5. BMAD auto-manifest (`silverline/reporting/bmad.py` + `silverline-manifest-from-bmad`)

Reads the standard Silverline BMAD layout and emits `scripts/requirements_manifest.py`:

| Source | Used for |
|---|---|
| `_bmad-output/planning-artifacts/**/PRD.md` | FR id, description, priority, **explicit `[Phase N]` marker**, category grouping |
| `_bmad-output/test-artifacts/requirement-traceability-matrix.md` | FR → story → scenario links |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | FR **status** from story state |

**FR → Phase:** parsed from an explicit marker on each FR line in the PRD, e.g. `FR-012 [Phase 2] — Password reset via email`. Accepted spellings normalized by `Phase.parse`. **Absent marker → `Phase.MVP`.**

**FR → status** mapping from the FR's linked stories (via RTM):

| Story state(s) | FR status |
|---|---|
| all linked stories `done` | `Implemented` |
| any `in-progress` / `ready-for-dev` / `review` | `Planned` |
| only `backlog` (or no linked story) | `Backlog` |

**Category:** derived from the FR id's type segment (`FR-AUTH-01` → `AUTH`) or, for plain `FR-001` numbering, from the PRD's requirement section heading. The generator writes a `CATEGORIES` block with display names taken from those section headings.

CLI:
```
silverline-manifest-from-bmad \
  --bmad-root _bmad-output \
  --out scripts/requirements_manifest.py
```
Idempotent: regenerating overwrites the file; the file carries a "generated — do not edit by hand" banner. Projects that are not BMAD-shaped simply skip this and author the manifest by hand (legacy path still supported).

### 6. Updated reusable workflows

`silverline-ci-reusable.yml` stops depending on copied scripts:

```yaml
- run: pip install "git+https://github.com/Silverline-Software/cd-pipeline@${{ inputs.pipeline-ref }}"
- run: silverline-manifest-from-bmad --bmad-root _bmad-output --out scripts/requirements_manifest.py
  if: ${{ inputs.bmad }}
  continue-on-error: true
- run: silverline-release-notes --bdd-xml ... --features-dir ... --output-dir release/ ...
```

New inputs: `pipeline-ref` (default a pinned tag like `v1.0.0`) and `bmad` (boolean, default true). The CD/Firebase workflow (`silverline-cd-reusable.yml`) is unchanged — it operates on release assets, not the generator.

### 7. Deliverable — `silverline-release-reports-setup` skill

A reusable skill that wires any client repo in, in order:
1. Detect whether the repo is BMAD-shaped (`_bmad-output/` present).
2. Add the pinned `pip install` + `silverline-release-notes` (and, if BMAD, `silverline-manifest-from-bmad`) steps to CI — or switch the repo to *call* `silverline-ci-reusable.yml`.
3. Generate `scripts/requirements_manifest.py` from BMAD, or scaffold the hand-maintained template.
4. Verify acceptance scenarios are tagged `@FR-<...>` / `@req-<...>`; report untagged FRs.
5. Confirm the `release-notes-hosting` GitHub environment + `FIREBASE_PROJECT_ID` / `PROJECT_DISPLAY_NAME` + org `RELEASE_NOTES_GCP_SA_KEY`.
6. Run a local smoke `silverline-release-notes` and open the HTML to confirm phase grouping.

The skill references the README and the phase-aware HTML template as its source of truth.

---

## Testing

- **Unit:** `Phase.parse`/`label`/ordering; manifest loader (legacy 3-tuple + new 4-tuple, category-phase fallback); BMAD parsers (PRD FR + `[Phase N]` markers, RTM link extraction, sprint-status → status mapping) against fixture artifacts; HTML phase-section rendering (assert ascending order, empty-phase omission, per-phase rollups).
- **Acceptance (pytest-bdd):** existing report-generation scenarios extended with a phase-grouped feature; a new `epic`/feature covering `silverline-manifest-from-bmad` end-to-end on a fixture `_bmad-output/` tree.
- **Packaging smoke:** `pip install .` then invoke both console entrypoints; assert the thin `scripts/` shims still run.
- Markers follow the existing `@req-<CATEGORY>-<NUM>` convention, registered in `pytest.ini`.

## Migration / rollout

1. Package + entrypoints + phase enum + schema change land in cd-pipeline behind the shims (no consumer breakage).
2. Tag `v1.0.0`.
3. Update the two reusable workflows to pip-install the tag.
4. Ship the skill; onboard one real BMAD project (e.g. a Real Random repo) end-to-end as the proving ground.
5. Roll the skill across remaining client repos.

## Out of scope (noted, not built here)

- Filling the `NotImplementedError` stubs in `silverline/pipeline/deploy.py`.
- Publishing to public PyPI or a private index (revisit if git-tag install proves painful in CI).
- Non-BMAD auto-manifest sources.

---

## Additional improvements surfaced (candidate follow-ups)

- A `make report-from-bmad` target wrapping `silverline-manifest-from-bmad` + `silverline-release-notes`.
- Surface untagged-FR warnings as a CI annotation so coverage gaps are visible on every PR.
- Per-phase completion badges on the `/versions` index page.
