"""
file: silverline/pipeline/gates.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: CI deployment gate — blocks Firebase deploys from broken builds.

description:
    Provides the CIGate class that queries the GitHub Checks API to verify
    all CI checks passed for a given commit before allowing deployment to
    proceed. A GateResult value object carries the verdict and the raw
    check data for logging.

    The gate is the first step in every CD run. If it fails, none of the
    Firebase deployment steps execute.
"""

from __future__ import annotations

import subprocess
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GateStatus(str, Enum):
    """Possible outcomes of a CI gate evaluation.

    Attributes:
        PASSED: All checks completed successfully.
        FAILED: One or more checks reported a failure conclusion.
        INCOMPLETE: One or more checks are still in progress.
        NO_CHECKS: No check runs were found for the commit.
    """

    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    NO_CHECKS = "no_checks"


@dataclass(frozen=True)
class CheckRun:
    """A single GitHub Actions check run record.

    Attributes:
        name: Workflow job name, e.g. ``"Test Suite"``.
        status: GitHub check status: ``"queued"``, ``"in_progress"``,
            or ``"completed"``.
        conclusion: GitHub check conclusion when completed, e.g.
            ``"success"``, ``"failure"``, ``"skipped"``. ``None`` if
            the check has not yet completed.
    """

    name: str
    status: str
    conclusion: Optional[str]

    @property
    def is_complete(self) -> bool:
        """Whether the check run has finished executing.

        Returns:
            ``True`` when :attr:`status` is ``"completed"``.
        """
        return self.status == "completed"

    @property
    def is_passing(self) -> bool:
        """Whether the check run completed with an acceptable conclusion.

        Acceptable conclusions are ``success``, ``skipped``, and
        ``neutral`` — anything else (``failure``, ``timed_out``,
        ``cancelled``, etc.) is treated as a failure.

        Returns:
            ``True`` if the check is complete and its conclusion is
            acceptable.
        """
        return self.is_complete and self.conclusion in (
            "success",
            "skipped",
            "neutral",
        )


@dataclass
class GateResult:
    """The outcome of a :class:`CIGate` evaluation.

    Attributes:
        status: Overall gate verdict.
        checks: All check runs inspected during the evaluation.
        commit_sha: The commit SHA that was evaluated.
        excluded: Names of check runs excluded from the evaluation
            (e.g. the CD workflow itself to avoid self-blocking).
    """

    status: GateStatus
    checks: list[CheckRun] = field(default_factory=list)
    commit_sha: str = ""
    excluded: set[str] = field(default_factory=set)

    @property
    def passed(self) -> bool:
        """Convenience accessor for a passing gate.

        Returns:
            ``True`` when :attr:`status` is :attr:`GateStatus.PASSED`.
        """
        return self.status == GateStatus.PASSED

    @property
    def failures(self) -> list[CheckRun]:
        """Check runs that completed with a non-passing conclusion.

        Returns:
            Subset of :attr:`checks` that failed and were not excluded.
        """
        return [
            c for c in self.checks
            if c.name not in self.excluded and c.is_complete and not c.is_passing
        ]

    @property
    def incomplete(self) -> list[CheckRun]:
        """Check runs that have not yet completed.

        Returns:
            Subset of :attr:`checks` still in progress.
        """
        return [c for c in self.checks if not c.is_complete]


class CIGate:
    """Queries the GitHub Checks API to verify CI passed for a commit.

    The gate fetches all check runs associated with a commit SHA and
    evaluates them against an exclusion list (to avoid self-blocking
    when the CD workflow's own previous runs appear as failed checks).

    Args:
        repo: GitHub repository in ``owner/name`` format.
        excluded_checks: Set of check run names to ignore when
            evaluating failures. Defaults to excluding the CD workflow's
            own job name to prevent self-blocking on re-runs.

    Example:
        >>> gate = CIGate("Silverline-Software/my-project")
        >>> result = gate.evaluate("abc1234")
        >>> if not result.passed:
        ...     raise SystemExit(f"CI gate failed: {result.status}")
    """

    _DEFAULT_EXCLUDED = frozenset({"Deploy Release Reports"})

    def __init__(
        self,
        repo: str,
        excluded_checks: Optional[frozenset[str]] = None,
    ) -> None:
        self.repo = repo
        self.excluded = (
            excluded_checks
            if excluded_checks is not None
            else self._DEFAULT_EXCLUDED
        )

    def evaluate(self, commit_sha: str) -> GateResult:
        """Evaluate CI gate status for the given commit.

        Calls the GitHub API via the ``gh`` CLI (must be authenticated)
        and inspects every check run on *commit_sha*.

        Args:
            commit_sha: Full or abbreviated commit SHA to evaluate.

        Returns:
            A :class:`GateResult` with the verdict and raw check data.

        Raises:
            RuntimeError: If the GitHub API call fails.
        """
        raw = self._fetch_checks(commit_sha)
        checks = [
            CheckRun(
                name=r["name"],
                status=r["status"],
                conclusion=r.get("conclusion"),
            )
            for r in raw.get("check_runs", [])
        ]

        if not checks:
            return GateResult(
                status=GateStatus.NO_CHECKS,
                checks=checks,
                commit_sha=commit_sha,
                excluded=set(self.excluded),
            )

        relevant = [c for c in checks if c.name not in self.excluded]

        if any(not c.is_complete for c in relevant):
            status = GateStatus.INCOMPLETE
        elif any(not c.is_passing for c in relevant):
            status = GateStatus.FAILED
        else:
            status = GateStatus.PASSED

        return GateResult(
            status=status,
            checks=checks,
            commit_sha=commit_sha,
            excluded=set(self.excluded),
        )

    def _fetch_checks(self, commit_sha: str) -> dict:
        """Fetch raw check-run data from the GitHub API.

        Args:
            commit_sha: Commit SHA to query.

        Returns:
            Parsed JSON response from the GitHub Checks API.

        Raises:
            RuntimeError: If ``gh`` exits non-zero.
        """
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{self.repo}/commits/{commit_sha}/check-runs",
                "--paginate",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"GitHub API error: {result.stderr.strip()}"
            )
        return json.loads(result.stdout)
