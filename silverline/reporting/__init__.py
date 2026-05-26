# silverline/reporting/__init__.py
"""
file: silverline/reporting/__init__.py
author: Stephen Boyett

description:
    Public surface of the release-reporting package. Re-exports the
    package's stable API (the locked Phase enum today; the manifest loader,
    report builder, and schema helpers are added by later tasks). Imported
    by the console entrypoints and the thin scripts/ shims.

---
Copyright © 2026 Silverline Software LLC. All Rights Reserved.
---
"""
from silverline.reporting.phases import Phase  # noqa: F401
from silverline.reporting.manifest import Requirement, normalize_requirements, load_manifest_module  # noqa: F401
