"""
Root conftest — makes scripts/ and examples/ importable for all tests.

The generator imports `requirements_manifest` from scripts/. That file doesn't
exist in this template repo (projects copy it from examples/). We pre-load it
from examples/ into sys.modules before any test imports the generator, so
Python's module cache is hit instead of the scripts/ path search.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# examples/ must be first so requirements_manifest resolves from there
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "examples"))

# Pre-load into sys.modules so generate_release_notes' own sys.path.insert
# doesn't shadow it when it runs its module-level import.
import requirements_manifest  # noqa: E402, F401
