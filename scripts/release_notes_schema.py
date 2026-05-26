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
