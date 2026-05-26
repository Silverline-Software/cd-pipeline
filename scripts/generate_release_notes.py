"""Thin shim — generator now lives in silverline.reporting.generate.

Kept so `from generate_release_notes import ReportBuilder`, the CLI
subprocess tests, and the Makefile `generate` targets keep working.
"""
import sys

from silverline.reporting.generate import *  # noqa: F401,F403
from silverline.reporting.generate import ReportBuilder, main  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
