"""
Cannasol Functionality Reports — JSON Schema Definitions (v1)

Separated from the report generator for easy schema updates as the
Cannasol dashboard evolves. Each constant is a dict describing required
keys and their expected types; used by validate_report() for lightweight
structural checks (no jsonschema dependency).
"""

# ── Executive Report (required artifact) ──────────────────────────────────────

EXECUTIVE_REPORT_SCHEMA = {
    "schema_version": str,
    "report_type": str,
    "generated_at": str,
    "repository": {
        "owner": str,
        "name": str,
        "release_tag": str,
        "commit_sha": str,
    },
    "summary": {
        "total_scenarios": int,
        "passed": int,
        "failed": int,
        "skipped": int,
        "pass_rate": float,
        "overall_status": str,  # "passing" | "failing" | "partial"
    },
    "requirements": list,   # list of requirement objects
    "test_suites": list,    # list of suite objects
}

# ── Unit Test Summary (optional artifact) ─────────────────────────────────────

UNIT_TEST_SUMMARY_SCHEMA = {
    "schema_version": str,
    "report_type": str,
    "generated_at": str,
    "repository": {
        "owner": str,
        "name": str,
        "release_tag": str,
        "commit_sha": str,
    },
    "summary": {
        "total_tests": int,
        "passed": int,
        "failed": int,
        "errors": int,
        "skipped": int,
        "pass_rate": float,
    },
    "test_suites": list,
}

# ── Coverage Summary (optional artifact) ──────────────────────────────────────

COVERAGE_SUMMARY_SCHEMA = {
    "schema_version": str,
    "report_type": str,
    "generated_at": str,
    "repository": {
        "owner": str,
        "name": str,
        "release_tag": str,
        "commit_sha": str,
    },
    "coverage": {
        "tool": str,
        "overall": {
            "lines_pct": float,
            "branches_pct": float,
            "functions_pct": float,
            "statements_pct": float,
        },
    },
}


# ── Validation helper ─────────────────────────────────────────────────────────

def validate_report(data: dict, schema: dict, path: str = "") -> list[str]:
    """Return a list of structural errors (empty == valid).

    Checks that required keys exist and top-level types match.  Nested
    dicts are checked recursively; lists are only checked for presence.
    """
    errors: list[str] = []
    for key, expected in schema.items():
        full_key = f"{path}.{key}" if path else key
        if key not in data:
            errors.append(f"missing key: {full_key}")
            continue
        value = data[key]
        if isinstance(expected, dict):
            if not isinstance(value, dict):
                errors.append(f"{full_key}: expected dict, got {type(value).__name__}")
            else:
                errors.extend(validate_report(value, expected, full_key))
        elif isinstance(expected, type):
            if not isinstance(value, expected):
                # allow int where float is expected
                if expected is float and isinstance(value, int):
                    continue
                errors.append(
                    f"{full_key}: expected {expected.__name__}, "
                    f"got {type(value).__name__}"
                )
    return errors
