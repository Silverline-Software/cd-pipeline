"""
file: silverline/hosting/site.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: HostingSite value object describing a Firebase Hosting deployment.

description:
    HostingSite bundles the site identifier, the local public directory
    to deploy, and optional configuration overrides (cache headers,
    clean URLs) into a single value object passed to FirebaseClient.deploy().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CacheRule:
    """A cache-control rule for a set of URL patterns.

    Attributes:
        glob: Glob pattern matched against URL paths,
            e.g. ``"**/*.html"``.
        max_age: ``Cache-Control: max-age`` value in seconds.
            Use ``0`` for ``no-cache``.
        immutable: Whether to append the ``immutable`` directive.
            Only meaningful when *max_age* > 0.
    """

    glob: str
    max_age: int = 0
    immutable: bool = False

    @property
    def header_value(self) -> str:
        """Computed ``Cache-Control`` header value string.

        Returns:
            A ``Cache-Control`` value such as ``"no-cache"`` or
            ``"public, max-age=31536000, immutable"``.
        """
        if self.max_age == 0:
            return "no-cache"
        parts = [f"public", f"max-age={self.max_age}"]
        if self.immutable:
            parts.append("immutable")
        return ", ".join(parts)


_DEFAULT_CACHE_RULES: list[CacheRule] = [
    CacheRule(glob="**/*.html", max_age=0),
    CacheRule(glob="**/*.json", max_age=0),
    CacheRule(glob="**/*.css",  max_age=31_536_000, immutable=True),
    CacheRule(glob="**/*.js",   max_age=31_536_000, immutable=True),
]


@dataclass
class HostingSite:
    """Configuration for a single Firebase Hosting deployment.

    Passed to :meth:`~silverline.hosting.firebase.FirebaseClient.deploy`
    to describe what to deploy and how.

    Attributes:
        site_id: Firebase Hosting site ID, e.g. ``"my-project"``.
            Used as the ``site`` key in ``firebase.json`` when set.
        public_dir: Local directory whose contents will be deployed.
        clean_urls: Whether to strip ``.html`` extensions from URLs.
            Defaults to ``True``.
        cache_rules: Cache-control rules applied to matched URL patterns.
            Defaults to :data:`_DEFAULT_CACHE_RULES`.
        custom_domain: Optional vanity domain, e.g.
            ``"reports.myproject.com"``. Used for the deployment summary
            URL only — DNS must be configured separately in Firebase.
    """

    site_id: str
    public_dir: Path
    clean_urls: bool = True
    cache_rules: list[CacheRule] = field(
        default_factory=lambda: list(_DEFAULT_CACHE_RULES)
    )
    custom_domain: Optional[str] = None

    @property
    def base_url(self) -> str:
        """Public base URL for this hosting site.

        Returns the custom domain if configured, otherwise the default
        ``*.web.app`` URL.

        Returns:
            Base URL string without a trailing slash.
        """
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return f"https://{self.site_id}.web.app"

    def to_firebase_config(self) -> dict:
        """Serialise this site into a ``firebase.json`` hosting block.

        Returns:
            A dictionary suitable for JSON serialisation as the
            ``"hosting"`` value in ``firebase.json``.
        """
        config: dict = {
            "public": str(self.public_dir),
            "ignore": ["firebase.json", "**/.*"],
            "cleanUrls": self.clean_urls,
            "headers": [
                {
                    "source": rule.glob,
                    "headers": [
                        {"key": "Cache-Control", "value": rule.header_value}
                    ],
                }
                for rule in self.cache_rules
            ],
        }
        if self.site_id:
            config["site"] = self.site_id
        return config
