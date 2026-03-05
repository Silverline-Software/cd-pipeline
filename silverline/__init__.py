"""
file: silverline/__init__.py
author: Stephen Boyett
company: Silverline Software
date: 2026-03-05
version: 1.0
brief: Silverline CD Pipeline — public package interface.

description:
    Root package for the Silverline release automation toolkit.
    Exposes the top-level pipeline, hosting, and gate interfaces
    used by the CD workflow to deploy branded release reports to
    Firebase Hosting.
"""

from silverline.pipeline.deploy import DeploymentPipeline
from silverline.pipeline.release import Release, ReleaseTag
from silverline.pipeline.gates import CIGate, GateResult

__all__ = [
    "DeploymentPipeline",
    "Release",
    "ReleaseTag",
    "CIGate",
    "GateResult",
]

__version__ = "1.0.0"
__author__ = "Stephen Boyett"
__company__ = "Silverline Software"
