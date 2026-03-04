"""
Requirements manifest — EXAMPLE TEMPLATE.

Copy this file to your project's `scripts/requirements_manifest.py` and
customize the phases, categories, and requirements for your project.

The report generator reads PHASES, CATEGORIES, REQUIREMENTS, and
normalize_tag() from this module.
"""

# ── Phases ────────────────────────────────────────────────────────────────────
# Group requirements into delivery phases. At minimum, define one phase.

PHASES = {
    1: {
        "name": "Phase 1 — MVP",
        "description": "Core features for initial launch.",
    },
    2: {
        "name": "Phase 2 — Enhancements",
        "description": "Post-launch improvements and advanced features.",
    },
}

# ── Categories ────────────────────────────────────────────────────────────────
# Group requirements by functional area.  The key becomes the tag prefix
# (e.g. "AUTH" matches tags @req-AUTH-01 or @FR-AUTH-01).
#
# "order" controls display position within a phase.

CATEGORIES = {
    "AUTH": {
        "name": "Authentication",
        "description": "User registration, login, and session management.",
        "phase": 1,
        "order": 1,
    },
    "DASH": {
        "name": "Dashboard",
        "description": "User-facing dashboard and account management.",
        "phase": 1,
        "order": 2,
    },
    "ADMIN": {
        "name": "Admin",
        "description": "Administrative capabilities and oversight.",
        "phase": 1,
        "order": 3,
    },
    # Add more categories as needed...
}

# ── Individual Requirements ───────────────────────────────────────────────────
# Key:   Normalized ID with category prefix (e.g. "AUTH-01")
# Value: (description, priority, status)
#   priority: P0 = Must Have, P1 = Should Have, P2 = Nice to Have
#   status:   Implemented | Planned | Backlog

REQUIREMENTS: dict[str, tuple[str, str, str]] = {
    # ── AUTH ──────────────────────────────────────────────────────────────
    "AUTH-01": ("User can register with email and password", "P0", "Implemented"),
    "AUTH-02": ("User can log in with valid credentials", "P0", "Implemented"),
    "AUTH-03": ("User can log out", "P0", "Implemented"),
    "AUTH-04": ("Password reset via email link", "P0", "Planned"),

    # ── DASH ─────────────────────────────────────────────────────────────
    "DASH-01": ("View account information", "P0", "Implemented"),
    "DASH-02": ("Edit profile settings", "P1", "Planned"),

    # ── ADMIN ────────────────────────────────────────────────────────────
    "ADMIN-01": ("Admin can view all users", "P0", "Implemented"),
    "ADMIN-02": ("Admin can disable accounts", "P0", "Planned"),
}


# ── Lookup helpers ────────────────────────────────────────────────────────────


def normalize_tag(tag: str) -> str:
    """Strip tag prefix to get normalized requirement ID.

    Handles both @req-AUTH-01 and @FR-AUTH-01 conventions.
    Extend this if your project uses a different prefix.
    """
    return tag.replace("req-", "").replace("FR-", "")


def get_category_key(tag: str) -> str:
    """Extract category from a tag string."""
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
