"""
file: silverline/hosting/firebase.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: FirebaseClient — wraps firebase-tools CLI for Python callers.

description:
    Provides a thin Python wrapper around the Firebase CLI (firebase-tools)
    for Hosting operations: ensuring a site exists (idempotent create) and
    deploying a public directory to a configured site. Authentication is
    handled externally via GOOGLE_APPLICATION_CREDENTIALS or firebase login.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from silverline.hosting.site import HostingSite


class FirebaseError(Exception):
    """Raised when a Firebase CLI command exits with a non-zero status.

    Attributes:
        command: The CLI command that failed.
        returncode: Exit code from the subprocess.
        stderr: Captured standard error output.
    """

    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"firebase {command[1]!r} failed (exit {returncode}): {stderr.strip()}"
        )


class FirebaseClient:
    """Python interface to the Firebase CLI for Hosting operations.

    Wraps ``firebase-tools`` (must be installed and on PATH) to provide
    idempotent site provisioning and directory deployment.

    Args:
        project: Firebase project ID, e.g. ``"silverline-release-hub"``.
        site_id: Optional site ID for multi-site Hosting. When ``None``,
            the project's default site is used.

    Example:
        ::

            client = FirebaseClient(
                project="silverline-release-hub",
                site_id="my-project",
            )
            client.ensure_site_exists()
            client.deploy(site)
    """

    def __init__(self, project: str, site_id: Optional[str] = None) -> None:
        self.project = project
        self.site_id = site_id

    @property
    def base_url(self) -> str:
        """Default public URL for this client's Hosting site.

        Returns:
            ``https://<site_id>.web.app`` when a site ID is configured,
            otherwise ``https://<project>.web.app``.
        """
        target = self.site_id or self.project
        return f"https://{target}.web.app"

    def ensure_site_exists(self) -> bool:
        """Create the Firebase Hosting site if it does not already exist.

        Queries the Firebase Hosting Sites API and creates the site only
        when absent — safe to call on every CD run.

        Returns:
            ``True`` if the site was created, ``False`` if it already
            existed.

        Raises:
            FirebaseError: If the site creation API call fails for any
                reason other than the site already existing.
            ValueError: If :attr:`site_id` is not set (no site to create).
        """
        if not self.site_id:
            raise ValueError("site_id must be set to call ensure_site_exists()")

        check = self._run(
            ["firebase", "hosting:sites:get", self.site_id,
             "--project", self.project],
            check=False,
        )
        if check.returncode == 0:
            return False  # Already exists

        self._run(
            ["firebase", "hosting:sites:create", self.site_id,
             "--project", self.project],
        )
        return True

    def deploy(self, site: HostingSite) -> None:
        """Deploy a :class:`~silverline.hosting.site.HostingSite` to Firebase.

        Writes a temporary ``firebase.json``, then invokes
        ``firebase deploy --only hosting`` from the site's public
        directory.

        Args:
            site: Configured site to deploy, including the local
                :attr:`~silverline.hosting.site.HostingSite.public_dir`.

        Raises:
            FirebaseError: If the ``firebase deploy`` command fails.
        """
        config = {"hosting": site.to_firebase_config()}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as fh:
            json.dump(config, fh, indent=2)
            config_path = fh.name

        try:
            self._run(
                [
                    "firebase", "deploy",
                    "--only", "hosting",
                    "--project", self.project,
                    "--config", config_path,
                ],
            )
        finally:
            Path(config_path).unlink(missing_ok=True)

    def _run(
        self,
        cmd: list[str],
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Execute a subprocess command.

        Args:
            cmd: Command and arguments list.
            check: If ``True`` (default), raise :class:`FirebaseError`
                on non-zero exit. If ``False``, return the result
                regardless of exit code.

        Returns:
            Completed process result.

        Raises:
            FirebaseError: If *check* is ``True`` and the command exits
                non-zero.
        """
        result = subprocess.run(cmd, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise FirebaseError(cmd, result.returncode, result.stderr)
        return result
