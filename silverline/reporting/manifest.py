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
