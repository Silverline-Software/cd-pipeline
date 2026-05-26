# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Silverline CD Pipeline — reusable infrastructure for generating branded release notes from test results and deploying them to Firebase Hosting with versioned URLs. Each release gets a permanent URL at `/<env>/<version>/` with a version switcher, and reports show requirement coverage with expandable Gherkin scenarios.

This repo is both a **library** (the `silverline/` package) and a **toolkit** (scripts + reusable GitHub Actions workflows that other Silverline projects consume).

## Build & Test Commands

```bash
make test                # Run all tests (unit + acceptance)
make test-unit           # Run unit tests only
make test-acceptance     # Run acceptance tests only (requires pytest-bdd)
make lint                # Lint Python scripts with ruff (falls back to flake8/pyflakes)
make validate            # Validate requirements_manifest.py structure
make check               # Run validate + lint
make generate            # Generate release notes from test results
make generate-example    # Generate sample report using example manifest
make clean               # Remove generated report files in release/
```

Single test file:
```bash
python3 -m pytest test/unit/test_schema.py -v
python3 -m pytest test/acceptance/test_report_generation.py -v
```

Single test by marker:
```bash
python3 -m pytest -m req-GEN-01 -v
```

Dependencies: `pip install pytest pytest-bdd`

## Architecture

### Python Package (`silverline/`)

The `silverline` package models the CD pipeline as composable dataclasses:

- **`pipeline/release.py`** — `ReleaseTag` (parses `<env>-vX.Y.Z[-rc]` tag convention) and `Release` (GitHub release with report assets)
- **`pipeline/gates.py`** — `CIGate` queries GitHub Checks API to block deploys from broken builds. `GateResult` carries the verdict. Excludes the CD workflow's own job ("Deploy Release Reports") to avoid self-blocking
- **`pipeline/deploy.py`** — `DeploymentPipeline` orchestrates: gate check → download reports → deploy docs → inject version switcher → generate versions index → Firebase push. Several methods are `NotImplementedError` stubs
- **`hosting/firebase.py`** — `FirebaseClient` wraps `firebase-tools` CLI for idempotent site creation and deployment
- **`hosting/site.py`** — `HostingSite` value object with cache rules, serializes to `firebase.json` hosting config

### Reporting Package (`silverline/reporting/`)

The source of truth for report generation is the `silverline.reporting` package:

- **`phases.py`** — `Phase` enum (locked, `MVP=0` … `PHASE_10`); `Phase.parse()` normalizes spellings and non-string inputs; `Phase.label` renders `"MVP"` or `"Phase N"`
- **`manifest.py`** — `load_manifest_module()` discovers `requirements_manifest.py` from CWD (sys.modules first, then `CWD/scripts/`, then `CWD/`); `normalize_requirements()` converts manifest entries into `Requirement` dataclasses, supporting both the 3-tuple (inherits category phase) and 4-tuple `(description, priority, status, phase)` forms
- **`schema.py`** — JSON schema definitions and `validate_report()` structural validator
- **`generate.py`** — orchestrates manifest loading, Gherkin/JUnit parsing, and HTML/JSON output; grouped Phase → Category → Requirement

The `silverline-release-notes` console entrypoint (installed via `pyproject.toml`) invokes `silverline.reporting.generate` directly.

### Scripts (`scripts/`)

- **`generate_release_notes.py`** — Thin re-export shim kept for backward compatibility; delegates to `silverline.reporting.generate`. Loads `requirements_manifest.py` from the **caller's repo** (`CWD/scripts/`), not from this repo's scripts dir
- **`release_notes_schema.py`** — Thin re-export shim; delegates to `silverline.reporting.schema`
- **`requirements_manifest.py`** — This repo's own manifest. Consumer projects copy from `examples/` and customize. Defines `PHASES`, `CATEGORIES`, `REQUIREMENTS`, and `normalize_tag()`
- **`ensure_firebase_site.sh`** — Idempotent Firebase site creation. Exits 0 on both "created" and "already exists"
- **`verify_ci_passed.sh`** — Deployment gate script. Uses `gh` CLI to check all CI runs passed

### Reusable GitHub Actions Workflows (`.github/workflows/`)

- **`silverline-ci-reusable.yml`** — Called by consumer projects' CI. Downloads test artifacts, runs `generate_release_notes.py`, uploads report artifact, attaches to GitHub Release on tag push
- **`silverline-cd-reusable.yml`** — Called on release publish. Verifies CI gate, downloads all release reports, injects version switcher bar, generates versions index, deploys everything to Firebase Hosting
- **`silverline-release-notes-cd.yml`** — This repo's own CD trigger (thin wrapper around `silverline-cd-reusable.yml`)
- **`silverline-release-documentation-ci.yml`** — This repo's own CI: runs tests, builds MkDocs API docs, generates report on tags

### Test Structure

Tests use **pytest-bdd** with Gherkin `.feature` files in `test/acceptance/features/`. All step definitions live in `test/acceptance/conftest.py` (shared across scenario files). Tests use mock `firebase`/`gh` executables injected via `PATH` for shell script testing.

- `test/conftest.py` — Adds `scripts/` and `examples/` to `sys.path`, pre-loads `requirements_manifest` from `examples/` into `sys.modules`
- `test/unit/` — Direct Python unit tests for schema validation, Gherkin parsing, JUnit parsing, report building
- `test/acceptance/` — BDD scenarios covering report generation, schema validation, Gherkin parsing, make targets, Firebase site provisioning, CI/CD deployment gate

Markers follow `@req-<CATEGORY>-<NUM>` convention (e.g., `@req-GEN-01`, `@req-CICD-001`). All markers are registered in `pytest.ini`.

## Tag Convention

Release tags encode environment + version: `<env>-vX.Y.Z[-rc]`. Bare tags (`v1.0.0`) default to `release` environment. The tag determines the Firebase Hosting URL path (e.g., `staging-v2.0.0-rc` → `/staging/v2.0.0/rc`).

## Key Patterns

- **Requirements manifest is loaded from CWD, not script dir** — `generate_release_notes.py` searches `Path.cwd()/scripts/` then `Path.cwd()` for `requirements_manifest.py`. Tests pre-load from `examples/` via conftest
- **Requirement tags**: Both `@req-<TYPE>-<NUM>` and `@FR-<TYPE>-<NUM>` prefixes are supported and normalized by `normalize_tag()`
- **CI gate self-exclusion**: The CD workflow's own job name "Deploy Release Reports" is always excluded from gate checks to prevent self-blocking on re-runs
- **Idempotent site provisioning**: `ensure_firebase_site.sh` and `FirebaseClient.ensure_site_exists()` both treat "already exists" as success
