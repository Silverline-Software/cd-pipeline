"""
file: silverline/pipeline/release.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: Release and ReleaseTag data models for the CD pipeline.

description:
    Defines the data structures used to represent GitHub releases and
    their parsed tag metadata throughout the CD pipeline. ReleaseTag
    handles the Silverline tag convention (env-vX.Y.Z[-rc]) and exposes
    the URL path segment used for Firebase Hosting directory layout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Tag pattern: <env>-vX.Y.Z[-rc]  or bare  vX.Y.Z[-rc]
_TAG_RE = re.compile(
    r"^(?:(?P<env>[a-z][a-z0-9-]*)-)?v(?P<version>\d+\.\d+\.\d+)(?P<rc>-rc)?$"
)

_DEFAULT_ENV = "release"


@dataclass(frozen=True)
class ReleaseTag:
    """A parsed Silverline release tag.

    Silverline uses structured git tags to encode the deployment
    environment and version in a single string. This class parses
    that convention and exposes the resulting components.

    Tag format::

        <env>-v<major>.<minor>.<patch>[-rc]

    Examples::

        release-v1.2.0         → env=release,  version=1.2.0, rc=False
        staging-v0.9.1-rc      → env=staging,  version=0.9.1, rc=True
        v2.0.0                 → env=release,  version=2.0.0, rc=False  (bare)

    Attributes:
        raw: The original tag string, e.g. ``"release-v1.0.0"``.
        env: Deployment environment name, e.g. ``"release"``.
        version: Semantic version string, e.g. ``"1.0.0"``.
        is_rc: Whether this is a release candidate.
    """

    raw: str
    env: str
    version: str
    is_rc: bool

    @classmethod
    def parse(cls, tag: str, default_env: str = _DEFAULT_ENV) -> "ReleaseTag":
        """Parse a raw git tag string into a :class:`ReleaseTag`.

        Args:
            tag: Raw git tag, e.g. ``"release-v1.2.3-rc"``.
            default_env: Environment name to use when the tag has no
                env prefix (bare tags like ``v1.0.0``). Defaults to
                ``"release"``.

        Returns:
            A populated :class:`ReleaseTag` instance.

        Raises:
            ValueError: If *tag* does not match the Silverline tag
                convention.

        Example:
            >>> t = ReleaseTag.parse("staging-v0.9.1-rc")
            >>> t.env, t.version, t.is_rc
            ('staging', '0.9.1', True)
        """
        m = _TAG_RE.match(tag)
        if not m:
            raise ValueError(
                f"Tag {tag!r} does not match Silverline convention "
                f"'[<env>-]vX.Y.Z[-rc]'"
            )
        return cls(
            raw=tag,
            env=m.group("env") or default_env,
            version=m.group("version"),
            is_rc=bool(m.group("rc")),
        )

    @property
    def path(self) -> str:
        """Firebase Hosting URL path segment for this release.

        Returns:
            Path string without leading or trailing slashes, e.g.
            ``"release/v1.0.0"`` or ``"staging/v0.9.1/rc"``.
        """
        base = f"{self.env}/v{self.version}"
        return f"{base}/rc" if self.is_rc else base

    def __str__(self) -> str:
        return self.raw


@dataclass
class Release:
    """A GitHub release with attached report assets.

    Represents one entry in the release history, combining the parsed
    :class:`ReleaseTag` with metadata fetched from the GitHub Releases
    API and the paths to downloaded report assets.

    Attributes:
        tag: Parsed release tag.
        published_at: UTC timestamp when the release was published.
        assets: Mapping of asset filename to local filesystem path.
        is_prerelease: Whether GitHub marked this as a pre-release.
        name: Human-readable release title from GitHub, if set.
    """

    tag: ReleaseTag
    published_at: datetime
    assets: dict[str, str] = field(default_factory=dict)
    is_prerelease: bool = False
    name: Optional[str] = None

    @property
    def has_report(self) -> bool:
        """Whether the release includes an HTML executive report.

        Returns:
            ``True`` if ``executive-report.html`` is present in
            :attr:`assets`.
        """
        return "executive-report.html" in self.assets

    @property
    def has_docs(self) -> bool:
        """Whether the release includes a built API docs site.

        Returns:
            ``True`` if ``docs-site.zip`` is present in :attr:`assets`.
        """
        return "docs-site.zip" in self.assets

    @property
    def label(self) -> str:
        """Display label for the version switcher dropdown.

        Returns:
            Version string with optional RC suffix, e.g. ``"v1.0.0"``
            or ``"v0.9.1 RC"``.
        """
        base = f"v{self.tag.version}"
        return f"{base} RC" if self.tag.is_rc else base
