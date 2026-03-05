"""
Requirements manifest for the Silverline CD Pipeline tool.

This manifest describes the tool itself — used when generating release reports
for this repo. Projects that consume this tool copy examples/requirements_manifest.py
to their own scripts/ and customise it for their domain.
"""

# ── Phases ────────────────────────────────────────────────────────────────────

PHASES = {
    1: {
        "name": "Phase 1 — v1.0 Core",
        "description": "Core report generation, schema validation, parsing, and developer automation.",
    },
}

# ── Categories ────────────────────────────────────────────────────────────────
# Keys must match the TYPE segment of @req-TYPE-NN tags in feature files.

CATEGORIES = {
    "GEN": {
        "name": "Report Generation",
        "description": "CLI script generates branded JSON and HTML release note artifacts from test results.",
        "phase": 1,
        "order": 1,
    },
    "SCHEMA": {
        "name": "Schema Validation",
        "description": "Lightweight structural validation of generated report JSON without external dependencies.",
        "phase": 1,
        "order": 2,
    },
    "PARSE": {
        "name": "Gherkin & JUnit Parsing",
        "description": "Parse .feature files for requirement traceability and JUnit XML for test results.",
        "phase": 1,
        "order": 3,
    },
    "MAKE": {
        "name": "Makefile Targets",
        "description": "Developer-facing make targets for report generation, validation, linting, and testing.",
        "phase": 1,
        "order": 4,
    },
    "SITE": {
        "name": "Firebase Site Provisioning",
        "description": "CD pipeline idempotently creates the Firebase Hosting site before deploying.",
        "phase": 1,
        "order": 5,
    },
}

# ── Requirements ──────────────────────────────────────────────────────────────
# Keys are the normalised IDs that match @req-TYPE-NN tags after stripping "req-".

REQUIREMENTS: dict[str, tuple[str, str, str]] = {
    # ── GEN ──────────────────────────────────────────────────────────────────
    "GEN-01": ("Generator produces executive-report.json with no test inputs", "P0", "Implemented"),
    "GEN-02": ("Generator produces executive-report.html with no test inputs", "P0", "Implemented"),
    "GEN-03": ("Generated JSON report contains the supplied release tag", "P0", "Implemented"),
    "GEN-04": ("Generated JSON report conforms to the executive report schema", "P0", "Implemented"),

    # ── SCHEMA ────────────────────────────────────────────────────────────────
    "SCHEMA-01": ("validate_report returns no errors for a structurally valid report", "P0", "Implemented"),
    "SCHEMA-02": ("validate_report reports errors for a report missing required keys", "P0", "Implemented"),
    "SCHEMA-03": ("validate_report accepts integer values where float is expected", "P1", "Implemented"),

    # ── PARSE ─────────────────────────────────────────────────────────────────
    "PARSE-01": ("GherkinParser extracts scenario names from .feature files", "P0", "Implemented"),
    "PARSE-02": ("GherkinParser associates @req-* and @FR-* tags with scenarios", "P0", "Implemented"),
    "PARSE-03": ("GherkinParser extracts Given/When/Then steps for each scenario", "P1", "Implemented"),
    "PARSE-04": ("JUnitParser extracts pass/fail totals from JUnit XML", "P0", "Implemented"),
    "PARSE-05": ("JUnitParser maps scenario names to pytest test function names", "P1", "Implemented"),

    # ── MAKE ──────────────────────────────────────────────────────────────────
    "MAKE-01": ("make generate-example produces report output files", "P0", "Implemented"),
    "MAKE-02": ("make validate exits 0 when requirements_manifest.py is present", "P0", "Implemented"),
    "MAKE-03": ("make lint exits 0 on project scripts", "P1", "Implemented"),

    # ── SITE ──────────────────────────────────────────────────────────────────
    "SITE-01": ("CD pipeline creates the Firebase Hosting site if it does not exist", "P0", "Implemented"),
    "SITE-02": ("CD pipeline is idempotent — re-running when site exists does not fail", "P0", "Implemented"),
    "SITE-03": ("CD pipeline fails loudly on unexpected Firebase errors", "P0", "Implemented"),
}


# ── Lookup helpers ────────────────────────────────────────────────────────────

def normalize_tag(tag: str) -> str:
    """Strip @req- or @FR- prefix to get normalised requirement ID."""
    return tag.replace("req-", "").replace("FR-", "")


def get_category_key(tag: str) -> str:
    """Extract category key (e.g. 'GEN') from a tag string."""
    normalized = normalize_tag(tag)
    parts = normalized.split("-")
    return parts[0] if parts else "OTHER"


def get_requirement(tag: str) -> dict | None:
    """Look up requirement metadata by tag string."""
    normalized = normalize_tag(tag)
    entry = REQUIREMENTS.get(normalized)
    if not entry:
        return None
    return {"description": entry[0], "priority": entry[1], "status": entry[2]}
