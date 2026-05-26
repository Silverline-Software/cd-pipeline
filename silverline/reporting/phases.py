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
    def parse(cls, value: object) -> "Phase":
        """Coerce a Phase/int/str to a Phase. Unrecognized input → MVP.

        Accepts Phase, an int phase value, or a string such as 'MVP',
        'Phase 2', 'phase-2', 'phase_2', 'phase2', or a bare '2'. Anything
        else — version strings, decimals, out-of-range numbers, junk —
        falls back to Phase.MVP.
        """
        if isinstance(value, Phase):
            return value
        if isinstance(value, bool):
            return cls.MVP
        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError:
                return cls.MVP
        s = str(value or "").strip().lower()
        if not s or s == "mvp":
            return cls.MVP
        m = re.fullmatch(r"(?:phase[\s_-]*)?(\d+)", s)
        if m:
            try:
                return cls(int(m.group(1)))
            except ValueError:
                return cls.MVP
        return cls.MVP
