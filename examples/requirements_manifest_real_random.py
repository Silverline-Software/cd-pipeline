"""
Requirements manifest for the Real Random Developer Portal.

Contains phase definitions, requirement categories, and individual FR metadata.
Update this file when requirements change. Requirement keys use normalized IDs
(e.g. "AUTH-01") — the lookup function handles tag prefix stripping.
"""

PHASES = {
    1: {
        "name": "Phase 1 — MVP Registration Portal",
        "description": (
            "Core registration portal delivering authentication, user and admin "
            "dashboards, email infrastructure, credential management, geo-restriction, "
            "and deployment infrastructure. Target: production-ready signup flow."
        ),
    },
    2: {
        "name": "Phase 2 — Advanced Features",
        "description": (
            "GitHub OAuth integration, per-app credential management, enhanced "
            "monitoring, email unsubscribe, and features deferred from Phase 1."
        ),
    },
}

# Categories ordered by logical flow through the application.
# "order" controls display position within a phase.
CATEGORIES = {
    "SIGNUP": {
        "name": "Signup-Only Registration",
        "description": "Streamlined pre-launch registration flow for early access signups before the full portal goes live.",
        "phase": 1,
        "order": 1,
    },
    "AUTH": {
        "name": "Authentication & Registration",
        "description": "User registration, login, password management, session handling, trial lifecycle, and account status management.",
        "phase": 1,
        "order": 2,
    },
    "CRED": {
        "name": "API Credential Management",
        "description": "Generation, display, regeneration, and revocation of API client credentials and trial access.",
        "phase": 1,
        "order": 3,
    },
    "DASH": {
        "name": "User Dashboard",
        "description": "Account information display, profile editing, usage statistics, trial status, and self-service features.",
        "phase": 1,
        "order": 4,
    },
    "ADMIN": {
        "name": "Admin Dashboard",
        "description": "Administrative user management, search/filter, account actions, and system oversight capabilities.",
        "phase": 1,
        "order": 5,
    },
    "EMAIL": {
        "name": "Email Infrastructure",
        "description": "Transactional email delivery for verification, password reset, trial notifications, and account alerts.",
        "phase": 1,
        "order": 6,
    },
    "EMAILINFRA": {
        "name": "Email Infrastructure (Technical)",
        "description": "SMTP configuration, DNS records (SPF/DKIM), sender routing, and delivery monitoring.",
        "phase": 1,
        "order": 7,
    },
    "GEO": {
        "name": "Geo-Restriction",
        "description": "IP-based geographic access control blocking registration from adversary nations.",
        "phase": 1,
        "order": 8,
    },
    "SEC": {
        "name": "Security",
        "description": "Password hashing, TLS, rate limiting, CSRF protection, input validation, secret management, and security headers.",
        "phase": 1,
        "order": 9,
    },
    "COMP": {
        "name": "Compliance",
        "description": "License agreement tracking, privacy policy access, and regulatory geo-restriction enforcement.",
        "phase": 1,
        "order": 10,
    },
    "UI": {
        "name": "UI Design",
        "description": "Visual design consistency, accessibility (WCAG AA), keyboard navigation, ARIA labels, and loading states.",
        "phase": 1,
        "order": 11,
    },
    "ARCH": {
        "name": "Architecture",
        "description": "Mock data layer, environment configuration, and API client interface patterns.",
        "phase": 1,
        "order": 12,
    },
    "PERF": {
        "name": "Performance",
        "description": "Page load time targets for registration flow and dashboard rendering.",
        "phase": 1,
        "order": 13,
    },
    "OBS": {
        "name": "Observability",
        "description": "Error capture, audit logging, delivery tracking, metrics collection, and alerting.",
        "phase": 1,
        "order": 14,
    },
    "INFRA": {
        "name": "Infrastructure",
        "description": "EC2 production setup, CI/CD pipeline, Nginx, HTTPS, secrets management, and database configuration.",
        "phase": 1,
        "order": 15,
    },
}

# ── Individual Requirements ───────────────────────────────────────────────────
# Key: normalized ID (tag with "req-" / "FR-" stripped)
# Value: (description, priority, status)
#   priority: P0 = Must Have, P1 = Should Have, P2 = Stretch/Pending
#   status:   Implemented | Planned | Backlog

REQUIREMENTS: dict[str, tuple[str, str, str]] = {
    # ── SIGNUP ────────────────────────────────────────────────────────────
    "SIGNUP-01": ("Signup page loads with registration form", "P0", "Implemented"),
    "SIGNUP-02": ("User can enter full name, email, and password", "P0", "Implemented"),
    "SIGNUP-03": ("Password confirmation field must match", "P0", "Implemented"),
    "SIGNUP-04": ("Email format validation on signup form", "P0", "Implemented"),
    "SIGNUP-05": ("Password strength requirements enforced", "P0", "Implemented"),
    "SIGNUP-06": ("Company name field on signup form", "P1", "Implemented"),
    "SIGNUP-07": ("Company type dropdown on signup form", "P1", "Implemented"),
    "SIGNUP-08": ("Country dropdown on signup form", "P1", "Implemented"),
    "SIGNUP-09": ("Phone number field on signup form (optional)", "P1", "Implemented"),
    "SIGNUP-10": ("License agreement checkbox required before registration", "P0", "Implemented"),
    "SIGNUP-11": ("License agreement full text viewable", "P0", "Implemented"),
    "SIGNUP-12": ("Successful registration shows confirmation message", "P0", "Implemented"),
    "SIGNUP-13": ("Duplicate email prevented with clear error", "P0", "Implemented"),
    "SIGNUP-14": ("Rate limiting on registration endpoint", "P0", "Implemented"),
    "SIGNUP-15": ("Geo-restriction blocks adversary nations", "P0", "Implemented"),
    "SIGNUP-16": ("Blocked users see appropriate error message", "P0", "Implemented"),
    "SIGNUP-17": ("Form validation errors displayed inline", "P0", "Implemented"),
    "SIGNUP-18": ("Registration page is mobile responsive", "P1", "Implemented"),
    "SIGNUP-20": ("Branding matches Real Random visual identity", "P1", "Implemented"),
    "SIGNUP-21": ("HTTPS enforced on all pages", "P0", "Implemented"),
    "SIGNUP-22": ("CSRF protection on registration form", "P0", "Implemented"),
    "SIGNUP-23": ("Verification email sent after registration", "P0", "Implemented"),

    # ── AUTH ───────────────────────────────────────────────────────────────
    "AUTH-01": ("User can register with email, password, and company information", "P0", "Implemented"),
    "AUTH-02": ("Password must be entered twice and must match", "P0", "Implemented"),
    "AUTH-03": ("Invalid passwords rejected with clear error message", "P0", "Implemented"),
    "AUTH-04": ("User must accept license agreement to register", "P0", "Implemented"),
    "AUTH-05": ("Rejecting the license agreement ends registration", "P0", "Implemented"),
    "AUTH-06": ("No user information retained if license is rejected", "P0", "Implemented"),
    "AUTH-07": ("User can re-register with same email after rejection", "P0", "Implemented"),
    "AUTH-08": ("Rate limiting on registration endpoint", "P0", "Implemented"),
    "AUTH-09": ("Email format and password strength validation", "P0", "Implemented"),
    "AUTH-10": ("Verification email sent upon registration", "P0", "Implemented"),
    "AUTH-11": ("Email verified via secure token link", "P0", "Implemented"),
    "AUTH-12": ("User can log in with email and password", "P0", "Implemented"),
    "AUTH-13": ("User can log out", "P0", "Implemented"),
    "AUTH-14": ("User can request password reset via email", "P0", "Implemented"),
    "AUTH-15": ("Forgot password button on login page", "P0", "Implemented"),
    "AUTH-16": ("Password reset email with secure link", "P0", "Implemented"),
    "AUTH-17": ("New password page displayed after reset link", "P0", "Implemented"),
    "AUTH-18": ("User can set new password via reset flow", "P0", "Implemented"),
    "AUTH-19": ("Invalid passwords rejected with requirements message", "P0", "Implemented"),
    "AUTH-20": ("Non-matching passwords rejected during reset", "P0", "Implemented"),
    "AUTH-21": ("Account creation date stored in database", "P0", "Implemented"),
    "AUTH-22": ("Trial end date stored in database", "P0", "Implemented"),
    "AUTH-23": ("Accounts auto-marked as expired when trial ends", "P0", "Implemented"),
    "AUTH-24": ("Trial expired users see clear messaging on login", "P0", "Implemented"),
    "AUTH-25": ("Expired users cannot access API", "P0", "Implemented"),
    "AUTH-26": ("Phone number field in registration (optional)", "P1", "Implemented"),
    "AUTH-27": ("Company type field in registration (optional)", "P1", "Implemented"),
    "AUTH-28": ("Country dropdown in registration", "P1", "Implemented"),
    "AUTH-29": ("Disabled users see suspension reason on login", "P0", "Implemented"),
    "AUTH-33": ("License agreement displays real Terms of Service", "P0", "Planned"),
    "AUTH-34": ("Suspended users can log in and view dashboard (read-only)", "P0", "Planned"),

    # ── CRED ──────────────────────────────────────────────────────────────
    "CRED-01": ("System generates API credentials upon first login after verification", "P0", "Implemented"),
    "CRED-02": ("Credentials displayed once in modal after verification", "P0", "Implemented"),
    "CRED-03": ("Modal includes warning about one-time display", "P0", "Implemented"),
    "CRED-04": ("Client secret never displayed again after modal dismissed", "P0", "Implemented"),
    "CRED-05": ("Client ID remains visible on dashboard", "P0", "Implemented"),
    "CRED-06": ("Credentials grant 30-day free trial access", "P0", "Implemented"),
    "CRED-07": ("User can regenerate credentials (revokes old, issues new)", "P0", "Implemented"),
    "CRED-08": ("Regeneration displays new secret in one-time modal", "P0", "Implemented"),
    "CRED-09": ("System warns user before credential regeneration", "P0", "Implemented"),

    # ── DASH ──────────────────────────────────────────────────────────────
    "DASH-01": ("View account info (name, email, license, company)", "P0", "Implemented"),
    "DASH-02": ("Edit account info (name, company; email triggers re-verify)", "P0", "Implemented"),
    "DASH-03": ("View Client ID (non-secret portion)", "P0", "Implemented"),
    "DASH-04": ("View API usage statistics", "P0", "Implemented"),
    "DASH-05": ("View trial status with days remaining", "P0", "Implemented"),
    "DASH-06": ("Regenerate API credentials from dashboard", "P0", "Implemented"),
    "DASH-07": ("Update settings (password, profile)", "P1", "Implemented"),
    "DASH-08": ("Automated emails about trial ending", "P2", "Backlog"),
    "DASH-09": ("Emails about Phase 2 upgrade options", "P2", "Backlog"),
    "DASH-10": ("Opt in/out of automated email service", "P2", "Backlog"),
    "DASH-11": ("Dashboard shows skeleton loading state", "P0", "Implemented"),
    "DASH-12": ("Dashboard shows appropriate empty state", "P0", "Implemented"),
    "DASH-13": ("Dashboard shows error state with retry button", "P0", "Implemented"),
    "DASH-14": ("Success toast notification when profile updated", "P1", "Implemented"),
    "DASH-15": ("Easy access to API documentation and support links", "P0", "Implemented"),
    "DASH-16": ("Customer support contact info visible", "P0", "Implemented"),
    "DASH-17": ("User can delete their account", "P0", "Implemented"),
    "DASH-18": ("Account deletion shows confirmation modal", "P0", "Implemented"),
    "DASH-19": ("Account deletion revokes all credentials", "P0", "Implemented"),
    "DASH-20": ("75% usage threshold request button", "P2", "Implemented"),
    "DASH-22": ("Quick Start guide with code examples", "P1", "Planned"),
    "DASH-23": ("Quick Start with multi-language examples", "P1", "Planned"),
    "DASH-24": ("FAQ content is current and accurate", "P1", "Planned"),

    # ── ADMIN ─────────────────────────────────────────────────────────────
    "ADMIN-01": ("Admin can view list of all users", "P0", "Implemented"),
    "ADMIN-02": ("Admin can view user's usage and limits", "P0", "Implemented"),
    "ADMIN-03": ("Admin can view user type and account info", "P0", "Implemented"),
    "ADMIN-04": ("Admin can view user's trial status", "P0", "Implemented"),
    "ADMIN-07": ("Comprehensive search/filter capabilities", "P1", "Implemented"),
    "ADMIN-08": ("Admin can reset user API credentials", "P0", "Implemented"),
    "ADMIN-09": ("Admin can disable user account", "P0", "Implemented"),
    "ADMIN-10": ("Admin can enable user account", "P0", "Implemented"),
    "ADMIN-11": ("Admin can suspend/revoke with reason", "P0", "Implemented"),
    "ADMIN-12": ("Admin can modify user status", "P0", "Implemented"),
    "ADMIN-13": ("Admin can modify user entropy limit", "P0", "Implemented"),
    "ADMIN-14": ("Admin can set trial end date via picker", "P0", "Implemented"),

    # ── EMAIL ─────────────────────────────────────────────────────────────
    "EMAIL-01": ("Email verification email sent on registration", "P0", "Implemented"),
    "EMAIL-02": ("Password reset email sent on request", "P0", "Implemented"),
    "EMAIL-03": ("Professionally branded email templates", "P1", "Implemented"),
    "EMAIL-04": ("Unsubscribe from optional emails", "P1", "Backlog"),
    "EMAIL-05": ("Trial expiration reminder emails (7, 3, 1 day)", "P1", "Implemented"),
    "EMAIL-06": ("Trial expired notification email", "P1", "Implemented"),
    "EMAIL-07": ("Account suspension notification email", "P0", "Implemented"),
    "EMAIL-08": ("75% usage threshold notification email", "P2", "Implemented"),
    "EMAIL-10": ("Email sender routing (support@silverlinesoftware.co)", "P1", "Planned"),

    # ── EMAILINFRA ────────────────────────────────────────────────────────
    "EMAILINFRA-01": ("SMTP backend configuration", "P0", "Implemented"),
    "EMAILINFRA-02": ("SPF/DKIM DNS records verified", "P0", "Implemented"),
    "EMAILINFRA-03": ("Emails sent from noreply@realrandom.co", "P0", "Implemented"),
    "EMAILINFRA-04": ("Email template branding applied", "P1", "Implemented"),
    "EMAILINFRA-05": ("Email delivery monitoring active", "P1", "Implemented"),

    # ── GEO ───────────────────────────────────────────────────────────────
    "GEO-01": ("Block registration from adversary nations (RU, CN, KP, IR, SY, CU)", "P0", "Implemented"),
    "GEO-02": ("Blocked users see appropriate error message", "P0", "Implemented"),

    # ── SEC ───────────────────────────────────────────────────────────────
    "SEC-01": ("Passwords stored using bcrypt/Argon2 hashing", "P0", "Implemented"),
    "SEC-02": ("All traffic over HTTPS (TLS 1.3)", "P0", "Implemented"),
    "SEC-03": ("Rate limiting on authentication endpoints", "P0", "Implemented"),
    "SEC-04": ("Secure session management", "P0", "Implemented"),
    "SEC-05": ("Input validation and sanitization", "P0", "Implemented"),
    "SEC-06": ("CSRF protection on all forms", "P0", "Implemented"),
    "SEC-07": ("API credentials never sent via email", "P0", "Implemented"),
    "SEC-08": ("Client secret displayed only once", "P0", "Implemented"),
    "SEC-09": ("Old client secret revoked on regeneration", "P0", "Implemented"),
    "SEC-11": ("Secrets never logged (redaction enforced)", "P1", "Implemented"),
    "SEC-12": ("Encryption at rest for database", "P0", "Implemented"),
    "SEC-13": ("Secrets managed via AWS Secrets Manager", "P0", "Implemented"),
    "SEC-14": ("Security headers (CSP, HSTS, X-Frame-Options)", "P0", "Implemented"),
    "SEC-15": ("AWS IAM least-privilege policies", "P1", "Implemented"),

    # ── COMP ──────────────────────────────────────────────────────────────
    "COMP-01": ("License agreement acceptance logged with timestamp", "P0", "Implemented"),
    "COMP-02": ("User has clear access to review license agreement", "P0", "Implemented"),
    "COMP-03": ("Geo-restriction enforced at registration", "P0", "Implemented"),
    "COMP-04": ("Basic privacy policy link available", "P0", "Implemented"),

    # ── UI ────────────────────────────────────────────────────────────────
    "UI-01": ("Dashboard easy to understand and navigate", "P0", "Implemented"),
    "UI-02": ("Modern interface matching realrandom.co visual identity", "P0", "Implemented"),
    "UI-03": ("Interactive but not flashy button styles", "P0", "Implemented"),
    "UI-04": ("Dashboards kept to single page layout", "P0", "Implemented"),
    "UI-05": ("All interactive elements have keyboard focus indicators", "P0", "Implemented"),
    "UI-06": ("Icon buttons have ARIA labels", "P0", "Implemented"),
    "UI-07": ("Color contrast meets WCAG AA (4.5:1 ratio)", "P0", "Implemented"),
    "UI-08": ("Loading states with skeleton shimmer animation", "P0", "Implemented"),

    # ── ARCH ──────────────────────────────────────────────────────────────
    "ARCH-01": ("Mock data toggle via USE_MOCK_DATA config", "P0", "Implemented"),
    "ARCH-02": ("Mock and real API clients implement identical interface", "P0", "Implemented"),
    "ARCH-03": ("Mock data layer completely removable", "P0", "Implemented"),
    "ARCH-04": ("USE_MOCK_DATA = true for dev/test environments", "P0", "Implemented"),
    "ARCH-05": ("USE_MOCK_DATA = false for production", "P0", "Implemented"),
    "ARCH-06": ("Environment-specific configuration via env vars", "P0", "Implemented"),

    # ── PERF ──────────────────────────────────────────────────────────────
    "PERF-01": ("Registration flow completes in under 5 seconds", "P0", "Implemented"),
    "PERF-02": ("Dashboard loads in under 3 seconds", "P0", "Implemented"),

    # ── OBS ───────────────────────────────────────────────────────────────
    "OBS-01": ("JavaScript errors captured with stack traces", "P1", "Implemented"),
    "OBS-02": ("Audit logging for security events", "P1", "Implemented"),
    "OBS-03": ("Email delivery status tracking", "P1", "Backlog"),
    "OBS-04": ("Application metrics collection", "P1", "Backlog"),
    "OBS-05": ("Critical errors trigger alerts", "P1", "Implemented"),

    # ── INFRA ─────────────────────────────────────────────────────────────
    "INFRA-01": ("Production Django setup on EC2", "P0", "Implemented"),
    "INFRA-02": ("Environment separation (dev/prod)", "P1", "Implemented"),
    "INFRA-03": ("CI/CD pipeline for automated testing", "P0", "Implemented"),
    "INFRA-04": ("Frontend served via Nginx on EC2", "P0", "Implemented"),
    "INFRA-05": ("HTTPS via Certbot/Let's Encrypt", "P0", "Implemented"),
    "INFRA-06": ("Secrets stored in AWS Secrets Manager", "P0", "Implemented"),
    "INFRA-07": ("Database with automated backups", "P0", "Implemented"),
}


# ── Lookup helpers ────────────────────────────────────────────────────────────


def normalize_tag(tag: str) -> str:
    """Strip tag prefix to get normalized requirement ID.

    req-ADMIN-01  → ADMIN-01
    FR-SIGNUP-01  → SIGNUP-01
    """
    return tag.replace("req-", "").replace("FR-", "")


def get_category_key(tag: str) -> str:
    """Extract category from a tag string.

    req-ADMIN-01  → ADMIN
    FR-SIGNUP-01  → SIGNUP
    """
    normalized = normalize_tag(tag)
    parts = normalized.split("-")
    # Handle multi-part category names like EMAILINFRA
    if normalized.startswith("EMAILINFRA"):
        return "EMAILINFRA"
    return parts[0] if parts else "OTHER"


def get_requirement(tag: str) -> dict | None:
    """Look up requirement metadata by tag string."""
    normalized = normalize_tag(tag)
    entry = REQUIREMENTS.get(normalized)
    if not entry:
        return None
    return {"description": entry[0], "priority": entry[1], "status": entry[2]}
