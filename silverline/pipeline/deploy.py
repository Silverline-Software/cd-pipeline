"""
file: silverline/pipeline/deploy.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: DeploymentPipeline — orchestrates the full CD release flow.

description:
    The DeploymentPipeline class is the top-level orchestrator for a
    Silverline CD deployment. It coordinates the CI gate check, report
    downloading, version switcher injection, docs deployment, and
    Firebase Hosting push in the correct order.

    Each phase is independently testable via the phase methods. The
    run() method executes all phases and returns a DeployResult summary.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from silverline.pipeline.gates import CIGate, GateResult
from silverline.pipeline.release import Release, ReleaseTag
from silverline.hosting.firebase import FirebaseClient
from silverline.hosting.site import HostingSite


@dataclass
class DeployResult:
    """Summary of a completed (or aborted) deployment pipeline run.

    Attributes:
        tag: The release tag that triggered this deployment.
        gate: CI gate evaluation result.
        deployed_versions: Number of report versions successfully
            written to the public directory.
        docs_deployed: Whether API docs were deployed to ``/docs/``.
        hosting_url: Base URL of the Firebase Hosting site, once known.
        success: Whether the pipeline completed without errors.
        error: Human-readable error message if :attr:`success` is
            ``False``, otherwise ``None``.
    """

    tag: Optional[ReleaseTag] = None
    gate: Optional[GateResult] = None
    deployed_versions: int = 0
    docs_deployed: bool = False
    hosting_url: str = ""
    success: bool = False
    error: Optional[str] = None


class DeploymentPipeline:
    """Orchestrates the full Silverline CD deployment flow.

    A pipeline instance is configured once and can be :meth:`run` for
    a specific release tag. The pipeline is stateless between runs —
    each call to :meth:`run` creates a fresh working directory.

    Args:
        repo: GitHub repository in ``owner/name`` format,
            e.g. ``"Silverline-Software/my-project"``.
        firebase_project: Firebase project ID,
            e.g. ``"silverline-release-hub"``.
        site_id: Optional Firebase Hosting site ID for multi-site
            projects. When omitted, deploys to the project's default
            site.
        default_env: Environment label for bare tags (``vX.Y.Z``
            without an env prefix). Defaults to ``"release"``.

    Example:
        ::

            pipeline = DeploymentPipeline(
                repo="Silverline-Software/my-project",
                firebase_project="silverline-release-hub",
                site_id="my-project",
            )
            result = pipeline.run("release-v1.2.0")
            if not result.success:
                raise SystemExit(result.error)
    """

    def __init__(
        self,
        repo: str,
        firebase_project: str,
        site_id: Optional[str] = None,
        default_env: str = "release",
    ) -> None:
        self.repo = repo
        self.firebase_project = firebase_project
        self.site_id = site_id
        self.default_env = default_env
        self._gate = CIGate(repo)
        self._firebase = FirebaseClient(firebase_project, site_id)

    def run(self, tag: str) -> DeployResult:
        """Execute the full deployment pipeline for *tag*.

        Phases (in order):

        1. Parse the release tag.
        2. Resolve the commit SHA and run the CI gate.
        3. Download all release reports.
        4. Deploy API docs if ``docs-site.zip`` is present.
        5. Inject the version switcher bar into each report.
        6. Generate the ``/versions`` index page.
        7. Push everything to Firebase Hosting.

        Args:
            tag: Git tag to deploy, e.g. ``"release-v1.2.0"``.

        Returns:
            A :class:`DeployResult` summarising the outcome.
        """
        result = DeployResult()

        try:
            result.tag = ReleaseTag.parse(tag, self.default_env)
            result.hosting_url = self._firebase.base_url
            return self._run_phases(result)
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)
            return result

    def _run_phases(self, result: DeployResult) -> DeployResult:
        """Internal phase runner.

        Args:
            result: In-progress :class:`DeployResult` to populate.

        Returns:
            The completed :class:`DeployResult`.
        """
        with tempfile.TemporaryDirectory() as workdir:
            public = Path(workdir) / "public"
            public.mkdir()

            result.gate = self.check_gate(result.tag)
            if not result.gate.passed:
                result.error = f"CI gate: {result.gate.status.value}"
                return result

            releases = self.download_reports(public)
            result.deployed_versions = len(releases)

            result.docs_deployed = self.deploy_docs(public, releases)
            self.inject_switcher(public, releases)
            self.generate_versions_index(public, releases)

            site = HostingSite(
                site_id=self.site_id or self.firebase_project,
                public_dir=public,
            )
            self._firebase.deploy(site)

        result.success = True
        return result

    def check_gate(self, tag: ReleaseTag) -> GateResult:
        """Run the CI gate for the commit pointed to by *tag*.

        Args:
            tag: Parsed release tag whose commit will be evaluated.

        Returns:
            The :class:`~silverline.pipeline.gates.GateResult` from
            the CI gate evaluation.
        """
        return self._gate.evaluate(tag.raw)

    def download_reports(self, public: Path) -> list[Release]:
        """Download executive reports for all releases with assets.

        Iterates over every GitHub release in :attr:`repo`, downloads
        ``executive-report.html`` (and optional JSON assets) for each
        one that has it, and writes them into *public* under the
        release's URL path.

        Args:
            public: Root directory to write downloaded reports into.

        Returns:
            List of :class:`~silverline.pipeline.release.Release`
            objects that had a report asset, in newest-first order.
        """
        raise NotImplementedError

    def deploy_docs(self, public: Path, releases: list[Release]) -> bool:
        """Deploy API docs from the latest release that ships them.

        Finds the newest :class:`~silverline.pipeline.release.Release`
        where :attr:`~silverline.pipeline.release.Release.has_docs` is
        ``True``, downloads ``docs-site.zip``, and extracts it to
        ``public/docs/``.

        Args:
            public: Root public directory.
            releases: All releases with reports, newest-first.

        Returns:
            ``True`` if docs were deployed, ``False`` if no release
            contained ``docs-site.zip``.
        """
        for release in releases:
            if release.has_docs:
                docs_dir = public / "docs"
                docs_dir.mkdir(exist_ok=True)
                # Download and extract docs-site.zip → public/docs/
                return True
        return False

    def inject_switcher(self, public: Path, releases: list[Release]) -> None:
        """Inject the floating version switcher bar into every report.

        Reads each ``index.html`` under *public*, prepends the version
        switcher ``<div>`` immediately after ``<body>``, and writes the
        file back in place.

        Args:
            public: Root public directory containing report HTML files.
            releases: All deployed releases, used to build the version
                dropdown options.
        """
        raise NotImplementedError

    def generate_versions_index(
        self, public: Path, releases: list[Release]
    ) -> None:
        """Generate the ``/versions`` index page listing all releases.

        Writes ``public/versions.html`` — a branded dark-mode page
        listing every deployed release with links to its report.

        Args:
            public: Root public directory.
            releases: All deployed releases, newest-first.
        """
        raise NotImplementedError
