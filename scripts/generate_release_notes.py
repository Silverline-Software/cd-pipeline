#!/usr/bin/env python3
"""
Generate Silverline Release Notes from test results.

Reads JUnit XML (BDD + Django), .feature files, and vitest coverage JSON,
then outputs standardized JSON + branded HTML reports.

All inputs are optional — the script gracefully produces partial reports
when files are missing.

Usage:
    python scripts/generate_release_notes.py \
        --bdd-xml test-results/results.xml \
        --backend-xml test-results/backend-results.xml \
        --features-dir test/acceptance/features/ \
        --coverage-json frontend/coverage/coverage-summary.json \
        --output-dir release/ \
        --owner Silverline-Software --repo real-random-portal \
        --release-tag registry-rc-v0.1.0 \
        --commit abc1234
"""

import argparse
import html as html_mod
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# Import schema definitions from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from release_notes_schema import (
    COVERAGE_SUMMARY_SCHEMA,
    EXECUTIVE_REPORT_SCHEMA,
    UNIT_TEST_SUMMARY_SCHEMA,
    validate_report,
)
from requirements_manifest import (
    CATEGORIES,
    PHASES,
    REQUIREMENTS,
    normalize_tag,
)

SCHEMA_VERSION = "1.0.0"

# ── HTML Report Stylesheet ────────────────────────────────────────────────────

_REPORT_CSS = """
:root {
    --bg-deep: #060609;
    --bg-primary: #0a0a10;
    --bg-surface: #0e0e1a;
    --bg-elevated: #141428;
    --border-subtle: #1a1a30;
    --border-medium: #252540;
    --text-primary: #d8d8e8;
    --text-secondary: #8888a0;
    --text-muted: #505068;
    --accent-green: #34d399;
    --accent-red: #f87171;
    --accent-amber: #fbbf24;
    --accent-blue: #60a5fa;
    --font-brand: 'Syncopate', 'Arial Black', sans-serif;
    --font-heading: 'Outfit', 'Helvetica Neue', sans-serif;
    --font-body: 'DM Sans', 'Helvetica', sans-serif;
    --font-mono: 'DM Mono', 'Menlo', monospace;
}
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: var(--font-body);
    background: var(--bg-deep);
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(40,40,80,0.35) 0%, transparent 70%),
        linear-gradient(180deg, var(--bg-deep) 0%, var(--bg-primary) 100%);
    background-attachment: fixed;
    color: var(--text-primary);
    line-height: 1.65;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
}
.report { max-width: 960px; margin: 0 auto; padding: 0 1.5rem 3rem; }

/* ── Header ── */
.report-header { text-align: center; padding: 3.5rem 0 2rem; }
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}
.brand-text {
    font-family: var(--font-brand);
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: 0.4em;
    background: linear-gradient(90deg, #555 0%, #666 30%, #909090 45%, #aaa 50%, #909090 55%, #666 70%, #555 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 8s ease-in-out infinite;
    margin-bottom: 0.75rem;
}
.silver-line {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #2a2a40 12%, #555 40%, #999 50%, #555 60%, #2a2a40 88%, transparent 100%);
    margin: 0.75rem auto;
    max-width: 400px;
}
.report-title {
    font-family: var(--font-heading);
    font-weight: 300;
    font-size: 2.2rem;
    color: var(--text-primary);
    margin: 1rem 0 1.25rem;
    letter-spacing: -0.02em;
}
.release-meta {
    display: flex;
    justify-content: center;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}
.meta-chip {
    font-size: 0.78rem;
    color: var(--text-secondary);
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 100px;
    padding: 0.3rem 0.85rem;
}
.meta-chip strong {
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    margin-right: 0.35rem;
}
.overall-status { margin-top: 0.25rem; }
.status-badge {
    display: inline-block;
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 0.82rem;
    letter-spacing: 0.18em;
    padding: 0.4rem 1.6rem;
    border-radius: 100px;
    border: 1px solid;
}
.status-badge--green {
    color: var(--accent-green);
    border-color: rgba(52,211,153,0.3);
    background: rgba(52,211,153,0.07);
    box-shadow: 0 0 24px rgba(52,211,153,0.08);
}
.status-badge--red {
    color: var(--accent-red);
    border-color: rgba(248,113,113,0.3);
    background: rgba(248,113,113,0.07);
    box-shadow: 0 0 24px rgba(248,113,113,0.08);
}
.status-badge--amber {
    color: var(--accent-amber);
    border-color: rgba(251,191,36,0.3);
    background: rgba(251,191,36,0.07);
    box-shadow: 0 0 24px rgba(251,191,36,0.08);
}
.status-badge--muted {
    color: var(--text-muted);
    border-color: rgba(80,80,104,0.3);
    background: rgba(80,80,104,0.06);
}

/* ── Navigation ── */
.toc {
    display: flex; justify-content: center; gap: 0.2rem;
    padding: 0.7rem 0; margin-bottom: 2.5rem;
    border-top: 1px solid var(--border-subtle);
    border-bottom: 1px solid var(--border-subtle);
}
.toc a {
    font-family: var(--font-heading);
    font-size: 0.78rem; font-weight: 500;
    color: var(--text-secondary); text-decoration: none;
    padding: 0.3rem 0.9rem; border-radius: 100px;
    transition: all 0.2s;
}
.toc a:hover { color: var(--text-primary); background: var(--bg-elevated); }

/* ── Sections ── */
.section { margin-bottom: 3rem; }
.section-title {
    font-family: var(--font-heading);
    font-weight: 600; font-size: 1.2rem;
    letter-spacing: 0.05em;
    color: var(--text-primary);
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}
.section .silver-line { margin: 0.4rem 0 1.5rem; max-width: 180px; margin-left: 0; }

/* ── Stat Cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.65rem;
}
.stat-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1.25rem 0.75rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.15s;
}
.stat-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--border-medium);
    transition: background 0.25s;
}
.stat-card:hover { border-color: var(--border-medium); transform: translateY(-1px); }
.stat-card--green::before { background: var(--accent-green); }
.stat-card--red::before { background: var(--accent-red); }
.stat-card--amber::before { background: var(--accent-amber); }
.stat-card--blue::before { background: var(--accent-blue); }
.stat-number {
    font-family: var(--font-heading);
    font-size: 1.85rem; font-weight: 700;
    line-height: 1; margin-bottom: 0.35rem;
}
.stat-label {
    font-size: 0.68rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500;
}
.stat-card--green .stat-number { color: var(--accent-green); }
.stat-card--red .stat-number { color: var(--accent-red); }
.stat-card--amber .stat-number { color: var(--accent-amber); }
.stat-card--blue .stat-number { color: var(--accent-blue); }

/* ── Suite Cards ── */
.suite-grid { display: grid; gap: 0.65rem; }
.suite-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px; padding: 1.25rem;
}
.suite-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.suite-header h3 { font-family: var(--font-heading); font-weight: 500; font-size: 0.95rem; }
.badge {
    font-family: var(--font-heading);
    font-size: 0.7rem; font-weight: 600;
    padding: 0.18rem 0.65rem; border-radius: 100px; letter-spacing: 0.03em;
}
.badge--green { color: var(--accent-green); background: rgba(52,211,153,0.1); }
.badge--red { color: var(--accent-red); background: rgba(248,113,113,0.1); }
.badge--amber { color: var(--accent-amber); background: rgba(251,191,36,0.1); }
.badge--muted { color: var(--text-muted); background: rgba(80,80,104,0.1); }
.progress-bar {
    height: 3px; background: var(--bg-elevated);
    border-radius: 2px; overflow: hidden; margin-bottom: 0.75rem;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-green), #6ee7b7);
    border-radius: 2px;
}
.suite-stats { display: flex; gap: 1.5rem; font-size: 0.76rem; color: var(--text-secondary); }

/* ── Filter Bar ── */
.filter-bar {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1.5rem; gap: 1rem;
}
.filter-input {
    width: 100%; max-width: 300px;
    padding: 0.45rem 0.9rem;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 8px; color: var(--text-primary);
    font-family: var(--font-body); font-size: 0.82rem;
    outline: none; transition: border-color 0.2s;
}
.filter-input:focus { border-color: var(--border-medium); }
.filter-input::placeholder { color: var(--text-muted); }
.help-btn {
    font-family: var(--font-heading); font-size: 0.72rem; font-weight: 500;
    color: var(--text-secondary); background: var(--bg-surface);
    border: 1px solid var(--border-subtle); border-radius: 100px;
    padding: 0.35rem 0.85rem; cursor: pointer;
    transition: all 0.2s; white-space: nowrap;
}
.help-btn:hover { color: var(--text-primary); border-color: var(--border-medium); }

/* ── Phase Blocks ── */
.phase-block { margin-bottom: 2.5rem; }
.phase-heading {
    font-family: var(--font-heading); font-weight: 600; font-size: 1.05rem;
    color: var(--text-primary); letter-spacing: 0.04em;
    margin-bottom: 0.3rem;
}
.phase-desc {
    font-size: 0.76rem; color: var(--text-secondary);
    margin-bottom: 1.25rem; line-height: 1.5;
}

/* ── Category Sections ── */
.category-section {
    margin-bottom: 0.65rem;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 10px; overflow: hidden;
}
.category-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.75rem 1.15rem; cursor: pointer;
    user-select: none; list-style: none;
}
.category-header::-webkit-details-marker { display: none; }
.category-header::before {
    content: '\\25B8'; margin-right: 0.5rem;
    font-size: 0.65rem; color: var(--text-muted);
    transition: transform 0.2s; display: inline-block;
}
.category-section[open] > .category-header::before { transform: rotate(90deg); }
.category-name {
    font-family: var(--font-heading); font-weight: 500; font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.category-subtitle {
    font-size: 0.7rem; color: var(--text-muted); font-weight: 400;
    letter-spacing: 0; text-transform: none; margin-left: 0.5rem;
}
.category-count {
    font-size: 0.7rem; color: var(--text-secondary); font-weight: 400;
}
.category-desc {
    font-size: 0.72rem; color: var(--text-muted);
    padding: 0 1.15rem 0.6rem;
    border-bottom: 1px solid var(--border-subtle);
    line-height: 1.45;
}

/* ── Requirement Items ── */
.req-item {
    border-bottom: 1px solid rgba(255,255,255,0.02);
}
.req-item:last-child { border-bottom: none; }
.req-item > summary {
    display: flex; align-items: center; gap: 0.55rem;
    padding: 0.5rem 1.15rem; cursor: pointer;
    user-select: none; list-style: none;
    transition: background 0.15s;
}
.req-item > summary::-webkit-details-marker { display: none; }
.req-item > summary:hover { background: rgba(255,255,255,0.015); }
.req-arrow {
    font-size: 0.55rem; color: var(--text-muted);
    transition: transform 0.2s; display: inline-block; width: 0.55rem; flex-shrink: 0;
}
.req-item[open] > summary .req-arrow { transform: rotate(90deg); }
.req-check {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1rem; height: 1rem; flex-shrink: 0;
    border-radius: 50%; font-size: 0.55rem; line-height: 1;
}
.req-check--passing {
    background: linear-gradient(135deg, #0d3320, #134e2e);
    color: var(--accent-green);
    box-shadow: 0 0 8px rgba(52,211,153,0.15);
}
.req-check--failing {
    background: linear-gradient(135deg, #3b1111, #4c1d1d);
    color: var(--accent-red);
    box-shadow: 0 0 8px rgba(248,113,113,0.15);
}
.req-check--untested {
    background: var(--bg-elevated);
    color: var(--text-muted);
}
.req-check--partial {
    background: linear-gradient(135deg, #3b2e0a, #4c3a14);
    color: var(--accent-amber);
}
.req-id {
    font-family: var(--font-mono); font-size: 0.72rem;
    color: var(--text-secondary); background: var(--bg-elevated);
    padding: 0.1rem 0.4rem; border-radius: 4px; white-space: nowrap;
}
.req-desc-text {
    flex: 1; font-size: 0.78rem; color: var(--text-secondary);
    min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.req-meta {
    display: flex; gap: 0.35rem; align-items: center; flex-shrink: 0;
}
.impl-badge {
    font-family: var(--font-mono); font-size: 0.56rem;
    padding: 0.06rem 0.3rem; border-radius: 3px;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.impl-badge--implemented { color: var(--accent-green); background: rgba(52,211,153,0.08); }
.impl-badge--planned { color: var(--accent-amber); background: rgba(251,191,36,0.08); }
.impl-badge--backlog { color: var(--text-muted); background: rgba(80,80,104,0.08); }
.priority-badge {
    font-family: var(--font-mono); font-size: 0.58rem;
    padding: 0.06rem 0.3rem; border-radius: 3px;
    color: var(--text-muted); background: rgba(80,80,104,0.12);
}
.sc-count-badge {
    font-family: var(--font-heading); font-size: 0.62rem; font-weight: 500;
    color: var(--text-muted); white-space: nowrap;
}

/* ── Scenario Items ── */
.req-scenarios {
    padding: 0.2rem 0 0.5rem 2.1rem;
}
.scenario-item {
    margin-bottom: 0.1rem;
    border-left: 2px solid var(--border-subtle);
}
.scenario-item > summary {
    display: flex; align-items: center; gap: 0.4rem;
    padding: 0.25rem 0.65rem; cursor: pointer;
    user-select: none; list-style: none; transition: all 0.15s;
}
.scenario-item > summary::-webkit-details-marker { display: none; }
.scenario-item > summary:hover { background: rgba(255,255,255,0.015); }
.scenario-arrow {
    font-size: 0.55rem; color: var(--text-muted); flex-shrink: 0;
    transition: transform 0.15s; display: inline-block;
}
.scenario-item[open] > summary .scenario-arrow { transform: rotate(90deg); }
.scenario-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.scenario-dot--passed { background: var(--accent-green); box-shadow: 0 0 6px rgba(52,211,153,0.4); }
.scenario-dot--failed { background: var(--accent-red); box-shadow: 0 0 6px rgba(248,113,113,0.4); }
.scenario-dot--unknown { background: var(--text-muted); }
.scenario-title {
    font-family: var(--font-heading); font-size: 0.74rem; font-weight: 400;
    color: var(--accent-green);
}
.scenario-title--failed { color: var(--accent-red); }
.scenario-title--unknown { color: var(--text-secondary); }
.scenario-feat {
    font-size: 0.62rem; color: var(--text-muted); margin-left: auto; white-space: nowrap;
}

/* ── Gherkin Steps ── */
.step-list {
    padding: 0.25rem 0 0.45rem 1.4rem;
}
.step {
    font-family: var(--font-mono); font-size: 0.7rem;
    color: var(--text-secondary); padding: 0.1rem 0; line-height: 1.45;
}
.step-kw {
    color: var(--accent-blue); font-weight: 500; margin-right: 0.25rem;
}
.no-scenarios {
    font-size: 0.72rem; color: var(--text-muted); font-style: italic;
    padding: 0.25rem 0 0.35rem 2.1rem;
}
.traceability-hint {
    font-size: 0.7rem; color: var(--text-muted); margin: 0.5rem 0 1rem;
    padding-left: 0.2rem;
}

/* ── Help Modal ── */
.help-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.7); z-index: 1000;
    align-items: center; justify-content: center;
}
.help-overlay.active { display: flex; }
.help-modal {
    background: var(--bg-surface);
    border: 1px solid var(--border-medium);
    border-radius: 12px; padding: 2rem;
    max-width: 560px; width: 90%; max-height: 80vh; overflow-y: auto;
}
.help-modal h3 {
    font-family: var(--font-heading); font-weight: 600;
    font-size: 1rem; margin-bottom: 1rem; color: var(--text-primary);
}
.help-modal p {
    font-size: 0.82rem; color: var(--text-secondary);
    margin-bottom: 0.75rem; line-height: 1.6;
}
.help-modal code {
    font-family: var(--font-mono); font-size: 0.75rem;
    background: var(--bg-elevated); padding: 0.1rem 0.35rem;
    border-radius: 3px; color: var(--accent-blue);
}
.help-close {
    font-family: var(--font-heading); font-size: 0.78rem;
    color: var(--text-secondary); background: var(--bg-elevated);
    border: 1px solid var(--border-subtle); border-radius: 8px;
    padding: 0.4rem 1.2rem; cursor: pointer;
    margin-top: 1rem; transition: all 0.2s;
}
.help-close:hover { color: var(--text-primary); border-color: var(--border-medium); }

/* ── Detail Results ── */
.detail-suite-name {
    font-family: var(--font-heading); font-weight: 500; font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 1.75rem 0 0.5rem; padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--border-subtle);
}
.feature-detail {
    margin-bottom: 0.25rem;
    border-left: 2px solid var(--border-subtle); margin-left: 0.5rem;
}
.feature-detail summary {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.35rem 0.75rem; cursor: pointer;
    font-size: 0.8rem; color: var(--text-secondary);
    user-select: none; list-style: none; transition: color 0.15s;
}
.feature-detail summary::-webkit-details-marker { display: none; }
.feature-detail summary:hover { color: var(--text-primary); }
.feature-name { font-family: var(--font-heading); font-weight: 400; }
.feature-count { font-size: 0.7rem; color: var(--text-muted); }
.scenario-table { width: 100%; border-collapse: collapse; margin-left: 0.5rem; }
.scenario-table td {
    padding: 0.2rem 0.5rem; font-size: 0.76rem; color: var(--text-secondary);
}
.scenario-table td:first-child { width: 1.5rem; }
.time-cell { text-align: right; color: var(--text-muted); font-size: 0.7rem; }
.status-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
}
.status-dot--green { background: var(--accent-green); box-shadow: 0 0 6px rgba(52,211,153,0.4); }
.status-dot--red { background: var(--accent-red); box-shadow: 0 0 6px rgba(248,113,113,0.4); }
.status-dot--amber { background: var(--accent-amber); box-shadow: 0 0 6px rgba(251,191,36,0.4); }
.status-dot--muted { background: var(--text-muted); }

/* ── Misc ── */
.empty-note { color: var(--text-muted); font-style: italic; font-size: 0.82rem; padding: 1rem 0; }
.report-footer {
    text-align: center; padding: 2rem 0 1rem;
    font-size: 0.76rem; color: var(--text-muted);
}
.report-footer .silver-line { max-width: 100%; margin-bottom: 1.5rem; }
.footer-brand {
    font-family: var(--font-brand); font-weight: 700;
    font-size: 0.6rem; letter-spacing: 0.35em;
    color: var(--text-muted); margin-top: 0.75rem; opacity: 0.5;
}

/* ── Animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.report-header { animation: fadeUp 0.6s ease; }
.section { animation: fadeUp 0.5s ease backwards; }
.section:nth-of-type(1) { animation-delay: 0.1s; }
.section:nth-of-type(2) { animation-delay: 0.15s; }
.section:nth-of-type(3) { animation-delay: 0.2s; }
.section:nth-of-type(4) { animation-delay: 0.25s; }

/* ── Print ── */
@media print {
    body { background: #fff; color: #1a1a1a; }
    .report { max-width: 100%; }
    .brand-text { -webkit-text-fill-color: #333; animation: none; }
    .silver-line { background: #ccc; }
    .toc, .filter-input { display: none; }
    .stat-card, .suite-card, .req-group { border-color: #ddd; background: #fafafa; }
    .stat-card--green .stat-number { color: #16a34a; }
    .stat-card--red .stat-number { color: #dc2626; }
    .stat-card--amber .stat-number { color: #d97706; }
    .stat-card--blue .stat-number { color: #2563eb; }
    .badge--green { color: #16a34a; background: #dcfce7; }
    .badge--red { color: #dc2626; background: #fee2e2; }
    .status-badge { border: 1px solid currentColor; background: transparent; box-shadow: none; }
    details[open] { page-break-inside: avoid; }
}
@media (max-width: 640px) {
    .stat-grid { grid-template-columns: repeat(2, 1fr); }
    .release-meta { flex-direction: column; align-items: center; }
    .toc { flex-wrap: wrap; }
}
"""


# ── Gherkin Parser ────────────────────────────────────────────────────────────


class GherkinParser:
    """Regex-based parser for .feature files.

    Extracts scenario names, tags (@req-*, @FR-*, @story-*, @ac-*),
    and step text (Given/When/Then/And/But).
    """

    TAG_RE = re.compile(r"@([\w-]+)")
    SCENARIO_RE = re.compile(
        r"^\s*Scenario(?:\s+Outline)?:\s*(.+)$", re.MULTILINE
    )
    STEP_RE = re.compile(
        r"^\s*(Given|When|Then|And|But)\s+(.+)$", re.MULTILINE
    )
    FEATURE_RE = re.compile(r"^\s*Feature:\s*(.+)$", re.MULTILINE)
    REQ_TAG_RE = re.compile(r"^(req-[\w-]+|FR-[\w-]+)$", re.IGNORECASE)

    def __init__(self):
        self.features: list[dict] = []

    def parse_dir(self, features_dir: Path) -> list[dict]:
        """Parse all .feature files in a directory."""
        self.features = []
        for fpath in sorted(features_dir.glob("*.feature")):
            self.features.append(self._parse_file(fpath))
        return self.features

    def _parse_file(self, fpath: Path) -> dict:
        text = fpath.read_text(encoding="utf-8")
        feature_match = self.FEATURE_RE.search(text)
        feature_name = feature_match.group(1).strip() if feature_match else fpath.stem

        scenarios = self._extract_scenarios(text)
        return {
            "file": fpath.name,
            "feature": feature_name,
            "scenarios": scenarios,
        }

    def _extract_scenarios(self, text: str) -> list[dict]:
        """Extract scenarios with their preceding tags and following steps."""
        scenarios = []
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Collect tags on consecutive tag lines
            tags = []
            while i < len(lines) and lines[i].strip().startswith("@"):
                tags.extend(self.TAG_RE.findall(lines[i]))
                i += 1
                if i >= len(lines):
                    break

            if i >= len(lines):
                break

            line = lines[i].strip()
            scenario_match = re.match(
                r"Scenario(?:\s+Outline)?:\s*(.+)$", line
            )
            if scenario_match:
                name = scenario_match.group(1).strip()
                steps = []
                i += 1
                # Collect steps until next scenario/feature or blank section
                while i < len(lines):
                    step_line = lines[i].strip()
                    if step_line.startswith(("Scenario", "Feature:", "@")):
                        break
                    step_match = re.match(
                        r"(Given|When|Then|And|But)\s+(.+)$", step_line
                    )
                    if step_match:
                        steps.append(
                            {
                                "keyword": step_match.group(1),
                                "text": step_match.group(2).strip(),
                            }
                        )
                    i += 1

                req_tags = [t for t in tags if self.REQ_TAG_RE.match(t)]
                story_tags = [t for t in tags if t.startswith("story-")]
                ac_tags = [t for t in tags if t.startswith("ac-")]

                scenarios.append(
                    {
                        "name": name,
                        "tags": tags,
                        "req_tags": req_tags,
                        "story_tags": story_tags,
                        "ac_tags": ac_tags,
                        "steps": steps,
                    }
                )
            else:
                i += 1

        return scenarios


# ── JUnit Parser ──────────────────────────────────────────────────────────────


class JUnitParser:
    """Parse JUnit XML testcases and correlate with Gherkin scenarios."""

    @staticmethod
    def scenario_to_test_name(scenario_name: str) -> str:
        """Convert Gherkin scenario name to pytest-bdd test function name.

        "User can register with valid information"
        → "test_user_can_register_with_valid_information"
        """
        name = scenario_name.lower()
        name = name.replace("-", " ")
        name = re.sub(r"[^a-z0-9\s]", "", name)
        name = re.sub(r"\s+", "_", name.strip())
        name = re.sub(r"_+", "_", name)
        return f"test_{name}"

    def parse(self, xml_path: Path) -> dict:
        """Parse a JUnit XML file and return structured results."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        suites = []
        total = passed = failed = skipped = errors = 0

        for testsuite in root.findall(".//testsuite"):
            suite_name = testsuite.get("name", "unknown")
            cases = []

            for tc in testsuite.findall("testcase"):
                classname = tc.get("classname", "")
                name = tc.get("name", "unknown")
                time_s = float(tc.get("time", 0))

                if tc.find("failure") is not None:
                    status = "failed"
                    message = (tc.find("failure").get("message", "") or "")[:200]
                elif tc.find("error") is not None:
                    status = "error"
                    message = (tc.find("error").get("message", "") or "")[:200]
                elif tc.find("skipped") is not None:
                    status = "skipped"
                    message = (tc.find("skipped").get("message", "") or "")[:200]
                else:
                    status = "passed"
                    message = ""

                cases.append(
                    {
                        "classname": classname,
                        "name": name,
                        "status": status,
                        "time": time_s,
                        "message": message,
                    }
                )
                total += 1
                if status == "passed":
                    passed += 1
                elif status == "failed":
                    failed += 1
                elif status == "skipped":
                    skipped += 1
                elif status == "error":
                    errors += 1

            suites.append({"name": suite_name, "testcases": cases})

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "suites": suites,
        }


# ── Report Builder ────────────────────────────────────────────────────────────


class ReportBuilder:
    """Orchestrate generation of all Silverline release note artifacts."""

    def __init__(
        self,
        owner: str,
        repo: str,
        release_tag: str,
        commit_sha: str,
        run_url: str = "",
    ):
        self.owner = owner
        self.repo = repo
        self.release_tag = release_tag
        self.commit_sha = commit_sha
        self.run_url = run_url
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def _repo_block(self) -> dict:
        return {
            "owner": self.owner,
            "name": self.repo,
            "release_tag": self.release_tag,
            "commit_sha": self.commit_sha,
        }

    # ── Executive Report ──────────────────────────────────────────────────

    def build_executive_report(
        self,
        bdd_results: dict | None,
        backend_results: dict | None,
        features: list[dict] | None,
    ) -> dict:
        """Build the executive-report.json (required artifact)."""
        # Merge BDD + backend totals
        total = passed = failed = skipped = 0
        if bdd_results:
            total += bdd_results["total"]
            passed += bdd_results["passed"]
            failed += bdd_results["failed"]
            skipped += bdd_results["skipped"]
        if backend_results:
            total += backend_results["total"]
            passed += backend_results["passed"]
            failed += backend_results["failed"]
            skipped += backend_results["skipped"]

        pass_rate = round((passed / total * 100), 2) if total > 0 else 0.0

        if failed > 0 or (bdd_results and bdd_results.get("errors", 0) > 0):
            overall_status = "failing"
        elif skipped > 0:
            overall_status = "partial"
        else:
            overall_status = "passing"

        # Build requirement traceability from features
        requirements = self._build_requirements(features, bdd_results)

        # Build test suites list
        test_suites = self._build_test_suites(bdd_results, backend_results, features)

        report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "executive-report",
            "generated_at": self.generated_at,
            "repository": self._repo_block(),
            "summary": {
                "total_scenarios": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": pass_rate,
                "overall_status": overall_status,
            },
            "requirements": requirements,
            "test_suites": test_suites,
        }

        errors = validate_report(report, EXECUTIVE_REPORT_SCHEMA)
        if errors:
            print(f"  Warning: executive report validation: {errors}")

        return report

    def _build_requirements(
        self,
        features: list[dict] | None,
        bdd_results: dict | None,
    ) -> list[dict]:
        """Extract requirement traceability from feature tags + test results."""
        if not features:
            return []

        # Build a lookup: test function name → pass/fail from JUnit
        test_status: dict[str, str] = {}
        if bdd_results:
            for suite in bdd_results.get("suites", []):
                for tc in suite.get("testcases", []):
                    test_status[tc["name"]] = tc["status"]

        # Collect requirements → scenarios
        req_map: dict[str, list[dict]] = {}
        for feat in features:
            for scenario in feat.get("scenarios", []):
                for tag in scenario.get("req_tags", []):
                    req_id = tag.upper().replace("REQ-", "req-")
                    # Normalize: keep original casing from tag
                    req_id = tag
                    if req_id not in req_map:
                        req_map[req_id] = []

                    # Determine scenario status from JUnit results
                    test_fn = JUnitParser.scenario_to_test_name(scenario["name"])
                    status = test_status.get(test_fn, "unknown")

                    req_map[req_id].append(
                        {
                            "scenario": scenario["name"],
                            "feature": feat["feature"],
                            "status": status,
                        }
                    )

        # Convert to list
        requirements = []
        for req_id, scenarios in sorted(req_map.items()):
            statuses = [s["status"] for s in scenarios]
            if all(s == "passed" for s in statuses):
                req_status = "passing"
            elif any(s in ("failed", "error") for s in statuses):
                req_status = "failing"
            elif all(s == "unknown" for s in statuses):
                req_status = "untested"
            else:
                req_status = "partial"

            requirements.append(
                {
                    "requirement_id": req_id,
                    "status": req_status,
                    "scenario_count": len(scenarios),
                    "scenarios": scenarios,
                }
            )

        return requirements

    def _build_test_suites(
        self,
        bdd_results: dict | None,
        backend_results: dict | None,
        features: list[dict] | None,
    ) -> list[dict]:
        """Build test_suites array for executive report."""
        suites = []

        if bdd_results:
            bdd_suite = {
                "name": "BDD Acceptance Tests",
                "type": "bdd",
                "total": bdd_results["total"],
                "passed": bdd_results["passed"],
                "failed": bdd_results["failed"],
                "skipped": bdd_results["skipped"],
                "scenarios": [],
            }
            for suite in bdd_results.get("suites", []):
                for tc in suite.get("testcases", []):
                    bdd_suite["scenarios"].append(
                        {
                            "name": tc["name"],
                            "classname": tc["classname"],
                            "status": tc["status"],
                            "time": tc["time"],
                        }
                    )
            suites.append(bdd_suite)

        if backend_results:
            backend_suite = {
                "name": "Django Backend Tests",
                "type": "unit",
                "total": backend_results["total"],
                "passed": backend_results["passed"],
                "failed": backend_results["failed"],
                "skipped": backend_results["skipped"],
                "scenarios": [],
            }
            for suite in backend_results.get("suites", []):
                for tc in suite.get("testcases", []):
                    backend_suite["scenarios"].append(
                        {
                            "name": tc["name"],
                            "classname": tc["classname"],
                            "status": tc["status"],
                            "time": tc["time"],
                        }
                    )
            suites.append(backend_suite)

        return suites

    # ── Unit Test Summary ─────────────────────────────────────────────────

    def build_unit_test_summary(self, backend_results: dict) -> dict:
        """Build unit-test-summary.json from Django test results."""
        suites = []
        for suite in backend_results.get("suites", []):
            suites.append(
                {
                    "name": suite["name"],
                    "tests": [
                        {
                            "name": tc["name"],
                            "classname": tc["classname"],
                            "status": tc["status"],
                            "time": tc["time"],
                            "message": tc.get("message", ""),
                        }
                        for tc in suite["testcases"]
                    ],
                }
            )

        total = backend_results["total"]
        passed = backend_results["passed"]
        pass_rate = round((passed / total * 100), 2) if total > 0 else 0.0

        report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "unit-test-summary",
            "generated_at": self.generated_at,
            "repository": self._repo_block(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": backend_results["failed"],
                "errors": backend_results["errors"],
                "skipped": backend_results["skipped"],
                "pass_rate": pass_rate,
            },
            "test_suites": suites,
        }

        errors = validate_report(report, UNIT_TEST_SUMMARY_SCHEMA)
        if errors:
            print(f"  Warning: unit test summary validation: {errors}")

        return report

    # ── Coverage Summary ──────────────────────────────────────────────────

    def build_coverage_summary(self, coverage_data: dict) -> dict:
        """Build coverage-summary.json from vitest coverage-summary.json."""
        totals = coverage_data.get("total", {})

        report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "coverage-summary",
            "generated_at": self.generated_at,
            "repository": self._repo_block(),
            "coverage": {
                "tool": "vitest",
                "overall": {
                    "lines_pct": totals.get("lines", {}).get("pct", 0.0),
                    "branches_pct": totals.get("branches", {}).get("pct", 0.0),
                    "functions_pct": totals.get("functions", {}).get("pct", 0.0),
                    "statements_pct": totals.get("statements", {}).get("pct", 0.0),
                },
            },
        }

        errors = validate_report(report, COVERAGE_SUMMARY_SCHEMA)
        if errors:
            print(f"  Warning: coverage summary validation: {errors}")

        return report

    # ── Executive HTML Report ────────────────────────────────────────────

    def build_executive_html(
        self, executive: dict, features: list[dict] | None = None
    ) -> str:
        """Build executive-report.html — branded Silverline HTML document.

        Uses the requirements manifest for phase-based organization with
        expandable requirements showing tagged Gherkin scenarios and steps.
        """
        esc = html_mod.escape
        s = executive["summary"]
        r = executive["repository"]
        suites = executive.get("test_suites", [])
        generated = executive["generated_at"]

        def _status_cls(status):
            return {
                "passing": "green", "failing": "red",
                "partial": "amber", "untested": "muted",
            }.get(status, "muted")

        # Build test function name → status from JUnit results
        test_status_map: dict[str, str] = {}
        for suite in suites:
            for sc in suite.get("scenarios", []):
                test_status_map[sc["name"]] = sc["status"]

        # Build requirement ID → list of scenarios (with steps) from features
        req_scenarios: dict[str, list[dict]] = {}
        if features:
            for feat in features:
                for scenario in feat.get("scenarios", []):
                    for tag in scenario.get("req_tags", []):
                        norm_id = normalize_tag(tag)
                        if norm_id not in req_scenarios:
                            req_scenarios[norm_id] = []
                        test_fn = JUnitParser.scenario_to_test_name(
                            scenario["name"]
                        )
                        status = test_status_map.get(test_fn, "unknown")
                        req_scenarios[norm_id].append({
                            "name": scenario["name"],
                            "feature": feat["feature"],
                            "status": status,
                            "steps": scenario.get("steps", []),
                        })

        # ── Summary cards ──
        status_color = _status_cls(s["overall_status"])
        status_upper = s["overall_status"].upper()

        summary_html = f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-number">{s['total_scenarios']}</div>
                <div class="stat-label">Total Scenarios</div>
            </div>
            <div class="stat-card stat-card--green">
                <div class="stat-number">{s['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card stat-card--red">
                <div class="stat-number">{s['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card stat-card--amber">
                <div class="stat-number">{s['skipped']}</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat-card stat-card--blue">
                <div class="stat-number">{s['pass_rate']}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>"""

        # ── Suite cards ──
        suite_cards = ""
        for suite in suites:
            st = suite.get("total", 0)
            sp = suite.get("passed", 0)
            sf = suite.get("failed", 0)
            pct = round(sp / st * 100, 1) if st else 0
            bcls = _status_cls("passing" if sf == 0 else "failing")
            suite_cards += f"""
            <div class="suite-card">
                <div class="suite-header">
                    <h3>{esc(suite['name'])}</h3>
                    <span class="badge badge--{bcls}">{sp}/{st}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{pct}%"></div>
                </div>
                <div class="suite-stats">
                    <span>Passed: {sp}</span>
                    <span>Failed: {sf}</span>
                    <span>Skipped: {suite.get('skipped', 0)}</span>
                </div>
            </div>"""

        # ── Requirement hierarchy: Phase → Category → Requirement → Scenario ──
        req_html = ""
        total_reqs = 0
        total_tested = 0

        for phase_num in sorted(PHASES.keys()):
            phase = PHASES[phase_num]
            phase_cats = sorted(
                [(k, v) for k, v in CATEGORIES.items()
                 if v["phase"] == phase_num],
                key=lambda x: x[1]["order"],
            )

            phase_content = ""
            for cat_key, cat in phase_cats:
                cat_reqs = sorted(
                    [(k, v) for k, v in REQUIREMENTS.items()
                     if k.startswith(cat_key + "-")],
                    key=lambda x: x[0],
                )
                if not cat_reqs:
                    continue

                cat_passing = 0
                cat_total = len(cat_reqs)
                total_reqs += cat_total
                req_items_html = ""

                for req_id, (desc, priority, impl_status) in cat_reqs:
                    scenarios = req_scenarios.get(req_id, [])

                    if scenarios:
                        total_tested += 1
                        statuses = [sc["status"] for sc in scenarios]
                        if all(st == "passed" for st in statuses):
                            test_st = "passing"
                            cat_passing += 1
                        elif any(
                            st in ("failed", "error") for st in statuses
                        ):
                            test_st = "failing"
                        else:
                            test_st = "partial"
                    else:
                        test_st = "untested"

                    # Build scenario HTML
                    scenarios_html = ""
                    if scenarios:
                        for sc in scenarios:
                            steps_html = ""
                            for step in sc.get("steps", []):
                                steps_html += (
                                    f'<div class="step">'
                                    f'<span class="step-kw">'
                                    f'{esc(step["keyword"])}</span>'
                                    f'{esc(step["text"])}</div>\n'
                                )

                            sc_status = sc["status"]
                            if sc_status == "passed":
                                dot_cls = "passed"
                                name_cls = ""
                            elif sc_status in ("failed", "error"):
                                dot_cls = "failed"
                                name_cls = " scenario-title--failed"
                            else:
                                dot_cls = "unknown"
                                name_cls = " scenario-title--unknown"

                            feat_short = sc["feature"]
                            if len(feat_short) > 45:
                                feat_short = feat_short[:42] + "..."

                            scenarios_html += (
                                f'<details class="scenario-item">'
                                f'<summary>'
                                f'<span class="scenario-arrow">&#9654;</span>'
                                f'<span class="scenario-dot '
                                f'scenario-dot--{dot_cls}"></span>'
                                f'<span class="scenario-title{name_cls}">'
                                f'{esc(sc["name"])}</span>'
                                f'<span class="scenario-feat">'
                                f'{esc(feat_short)}</span>'
                                f'</summary>'
                                f'<div class="step-list">{steps_html}'
                                f'</div></details>\n'
                            )
                    else:
                        scenarios_html = (
                            '<div class="no-scenarios">'
                            "No test scenarios tagged</div>"
                        )

                    check_sym = {
                        "passing": "\u2713",
                        "failing": "\u2717",
                        "partial": "~",
                        "untested": "\u2014",
                    }[test_st]

                    impl_cls = impl_status.lower()
                    sc_count = len(scenarios)
                    sc_label = (
                        f"{sc_count} scenario"
                        f"{'s' if sc_count != 1 else ''}"
                        if sc_count > 0
                        else ""
                    )

                    req_items_html += (
                        f'<details class="req-item">'
                        f'<summary>'
                        f'<span class="req-arrow">\u25B8</span>'
                        f'<span class="req-check req-check--{test_st}">'
                        f'{check_sym}</span>'
                        f'<code class="req-id">{esc(req_id)}</code>'
                        f'<span class="req-desc-text">'
                        f'{esc(desc)}</span>'
                        f'<span class="req-meta">'
                        f'<span class="impl-badge '
                        f'impl-badge--{impl_cls}">'
                        f'{esc(impl_status)}</span>'
                        f'<span class="priority-badge">'
                        f'{esc(priority)}</span>'
                        f'<span class="sc-count-badge">'
                        f'{sc_label}</span>'
                        f'</span>'
                        f'</summary>'
                        f'<div class="req-scenarios">'
                        f'{scenarios_html}</div>'
                        f'</details>\n'
                    )

                phase_content += (
                    f'<details class="category-section" open>'
                    f'<summary class="category-header">'
                    f'<span>'
                    f'<span class="category-name">{esc(cat_key)}</span>'
                    f'<span class="category-subtitle">'
                    f'\u2014 {esc(cat["name"])}</span>'
                    f'</span>'
                    f'<span class="category-count">'
                    f'{cat_passing}/{cat_total} tested &amp; passing'
                    f'</span>'
                    f'</summary>'
                    f'<div class="category-desc">'
                    f'{esc(cat["description"])}</div>'
                    f'{req_items_html}'
                    f'</details>\n'
                )

            if phase_content:
                req_html += (
                    f'<div class="phase-block">'
                    f'<h3 class="phase-heading">'
                    f'{esc(phase["name"])}</h3>'
                    f'<p class="phase-desc">'
                    f'{esc(phase["description"])}</p>'
                    f'{phase_content}'
                    f'</div>\n'
                )

        # ── Detailed results (by test suite / classname) ──
        details_html = ""
        for suite in suites:
            scenarios = suite.get("scenarios", [])
            if not scenarios:
                continue
            details_html += (
                f'<h3 class="detail-suite-name">{esc(suite["name"])}</h3>'
            )
            by_class: dict[str, list[dict]] = {}
            for sc in scenarios:
                by_class.setdefault(
                    sc.get("classname", "unknown"), []
                ).append(sc)

            for cn in sorted(by_class.keys()):
                items = by_class[cn]
                n_passed = sum(1 for x in items if x["status"] == "passed")
                has_fail = any(
                    x["status"] in ("failed", "error") for x in items
                )
                label = cn.split(".")[-1] if "." in cn else cn
                sc_rows = ""
                for sc in sorted(
                    items,
                    key=lambda x: (x["status"] != "failed", x["name"]),
                ):
                    dcls = _status_cls(
                        "failing"
                        if sc["status"] in ("failed", "error")
                        else "passing"
                        if sc["status"] == "passed"
                        else "amber"
                    )
                    tstr = (
                        f'{sc["time"]:.2f}s' if sc.get("time") else "-"
                    )
                    sc_rows += (
                        f'<tr><td><span class="status-dot '
                        f'status-dot--{dcls}"></span></td>'
                        f"<td>{esc(sc['name'])}</td>"
                        f'<td class="time-cell">{tstr}</td></tr>\n'
                    )
                open_attr = " open" if has_fail else ""
                details_html += (
                    f'<details class="feature-detail"{open_attr}>'
                    f"<summary>"
                    f'<span class="feature-name">{esc(label)}</span>'
                    f'<span class="feature-count">'
                    f"{n_passed}/{len(items)}</span>"
                    f"</summary>"
                    f'<table class="scenario-table">'
                    f"<tbody>{sc_rows}</tbody></table>"
                    f"</details>\n"
                )

        # ── Assemble document ──
        no_suites = (
            '<p class="empty-note">No test suite data available</p>'
            if not suites
            else ""
        )
        no_reqs = (
            '<p class="empty-note">No requirement data available</p>'
            if not REQUIREMENTS
            else ""
        )
        no_details = (
            '<p class="empty-note">No detailed results available</p>'
            if not suites
            else ""
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Functionality Report \u2014 {esc(r['name'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400&family=DM+Sans:wght@400;500&family=Outfit:wght@300;400;500;600;700&family=Syncopate:wght@700&display=swap" rel="stylesheet">
<style>{_REPORT_CSS}</style>
</head>
<body>
<div class="report">
    <header class="report-header">
        <div class="brand-text">SILVERLINE SOFTWARE</div>
        <div class="silver-line"></div>
        <h1 class="report-title">Functionality Report</h1>
        <div class="release-meta">
            <span class="meta-chip"><strong>Release</strong> {esc(r['release_tag'])}</span>
            <span class="meta-chip"><strong>Commit</strong> {esc(r['commit_sha'][:8])}</span>
            <span class="meta-chip"><strong>Generated</strong> {esc(generated[:19].replace('T',' '))}</span>
            {f'<a class="meta-chip" href="{esc(self.run_url)}" target="_blank" style="text-decoration:none"><strong>Pipeline</strong> View Run ↗</a>' if self.run_url else ''}
        </div>
        <div class="overall-status">
            <span class="status-badge status-badge--{status_color}">{status_upper}</span>
        </div>
    </header>

    <nav class="toc">
        <a href="#summary">Summary</a>
        <a href="#suites">Test Suites</a>
        <a href="#requirements">Requirements</a>
        <a href="#details">Details</a>
    </nav>

    <main>
        <section id="summary" class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="silver-line"></div>
            {summary_html}
        </section>

        <section id="suites" class="section">
            <h2 class="section-title">Test Suites</h2>
            <div class="silver-line"></div>
            <div class="suite-grid">{suite_cards}</div>
            {no_suites}
        </section>

        <section id="requirements" class="section">
            <h2 class="section-title">Requirement Traceability</h2>
            <div class="silver-line"></div>
            <div class="filter-bar">
                <input type="text" class="filter-input" placeholder="Filter requirements\u2026" oninput="filterReqs(this.value)">
                <button class="help-btn" onclick="document.getElementById('helpOverlay').classList.add('active')">What is this?</button>
            </div>
            <p class="traceability-hint">Click the &#9654; arrow next to each scenario to view the detailed test implementation for that requirement.</p>
            {req_html}
            {no_reqs}
        </section>

        <section id="details" class="section">
            <h2 class="section-title">Detailed Results</h2>
            <div class="silver-line"></div>
            {details_html}
            {no_details}
        </section>
    </main>

    <footer class="report-footer">
        <div class="silver-line"></div>
        <p>Generated by <strong>Silverline Software Report Automation</strong> v2.0.0</p>
        <p>{total_reqs} requirements \u00b7 {total_tested} with test coverage</p>
        <p class="footer-brand">SILVERLINE SOFTWARE</p>
    </footer>
</div>

<div class="help-overlay" id="helpOverlay" onclick="if(event.target===this)this.classList.remove('active')">
    <div class="help-modal">
        <h3>What is this report?</h3>
        <p>This <strong>Functionality Report</strong> traces every product requirement
        back to its automated acceptance tests using
        <strong>Behavior-Driven Development (BDD)</strong>.</p>
        <p>Requirements are tagged in test scenarios using identifiers like
        <code>@req-SIGNUP-01</code>. Each requirement can be expanded to see
        the specific scenarios that verify it, along with the
        <strong>Given / When / Then</strong> steps that describe expected behavior
        in plain language.</p>
        <p><strong>Status indicators:</strong></p>
        <p>\u2713 <strong>Passing</strong> \u2014 All tagged scenarios pass<br>
        \u2717 <strong>Failing</strong> \u2014 One or more scenarios fail<br>
        ~ <strong>Partial</strong> \u2014 Mixed results<br>
        \u2014 <strong>Untested</strong> \u2014 No test scenarios tagged yet</p>
        <button class="help-close" onclick="document.getElementById('helpOverlay').classList.remove('active')">Got it</button>
    </div>
</div>

<script>
function filterReqs(q) {{
    q = q.toLowerCase();
    document.querySelectorAll('.req-item').forEach(function(el) {{
        var match = el.textContent.toLowerCase().indexOf(q) > -1;
        el.style.display = match ? '' : 'none';
    }});
    document.querySelectorAll('.category-section').forEach(function(cat) {{
        var visible = cat.querySelectorAll('.req-item[style=""], .req-item:not([style])');
        var hasVisible = false;
        cat.querySelectorAll('.req-item').forEach(function(r) {{
            if (r.style.display !== 'none') hasVisible = true;
        }});
        cat.style.display = hasVisible ? '' : 'none';
    }});
}}
</script>
</body>
</html>"""


# ── Security scan helpers ─────────────────────────────────────────────────────


def parse_bandit_json(path):
    """Parse bandit -f json output into normalized findings."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    findings = []
    for r in data.get("results", []):
        findings.append({
            "severity": r.get("issue_severity", "LOW").upper(),
            "title": r.get("test_name", "unknown").replace("_", " ").title(),
            "location": f"{r.get('filename', '')}:{r.get('line_number', '')}",
            "description": r.get("issue_text", ""),
            "rule_id": r.get("test_id", ""),
            "scanner": "Bandit",
        })
    return findings


def parse_semgrep_json(path):
    """Parse semgrep --json output into normalized findings."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    SEV_MAP = {"WARNING": "MEDIUM", "ERROR": "HIGH", "INFO": "INFO", "NOTE": "LOW"}
    findings = []
    for r in data.get("results", []):
        extra = r.get("extra", {})
        raw_sev = extra.get("severity", extra.get("metadata", {}).get("severity", "INFO")).upper()
        sev = SEV_MAP.get(raw_sev, raw_sev)
        check_id = r.get("check_id", "")
        findings.append({
            "severity": sev,
            "title": check_id.split(".")[-1].replace("-", " ").replace("_", " ").title(),
            "location": f"{r.get('path', '')}:{r.get('start', {}).get('line', '')}",
            "description": extra.get("message", ""),
            "rule_id": check_id,
            "scanner": "Semgrep",
        })
    return findings


def render_security_section(all_findings):
    """Render the SECURITY SCAN RESULTS HTML section."""
    if not all_findings:
        return ""

    SEV_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    SEV_COLORS = {
        "CRITICAL": ("#ef4444", "239,68,68"),
        "HIGH": ("#f97316", "249,115,22"),
        "MEDIUM": ("#eab308", "234,179,8"),
        "LOW": ("#3b82f6", "59,130,246"),
        "INFO": ("#6b7280", "107,114,128"),
    }

    counts = {s: 0 for s in SEV_ORDER}
    for f in all_findings:
        sev = f.get("severity", "INFO").upper()
        if sev in counts:
            counts[sev] += 1

    # Summary badges
    badges = ""
    for sev in SEV_ORDER:
        if counts[sev] == 0:
            continue
        col, rgb = SEV_COLORS.get(sev, ("#6b7280", "107,114,128"))
        badges += (
            f'<span style="display:inline-flex;align-items:center;gap:0.3rem;'
            f'background:rgba({rgb},0.08);border:1px solid rgba({rgb},0.2);'
            f'border-radius:4px;padding:0.2rem 0.55rem;font-size:0.72rem;color:{col};">'
            f'<strong>{counts[sev]}</strong>&nbsp;{sev}</span>'
        )

    # Group by scanner
    scanners = {}
    for f in all_findings:
        scanners.setdefault(f["scanner"], []).append(f)

    scanner_html = ""
    for scanner_name, findings in scanners.items():
        sorted_findings = sorted(
            findings,
            key=lambda x: SEV_ORDER.index(x.get("severity", "INFO").upper())
            if x.get("severity", "INFO").upper() in SEV_ORDER else 99
        )
        rows = ""
        for f in sorted_findings:
            sev = f.get("severity", "INFO").upper()
            col, _ = SEV_COLORS.get(sev, ("#6b7280", "107,114,128"))
            rows += (
                f'<details class="scenario-item" style="margin-bottom:0.3rem;">'
                f'<summary style="cursor:pointer;list-style:none;display:flex;align-items:center;'
                f'gap:0.6rem;padding:0.5rem 0.75rem;background:var(--bg-raised);'
                f'border-radius:5px;border:1px solid var(--border-subtle);">'
                f'<span class="scenario-arrow">&#9654;</span>'
                f'<span style="font-size:0.65rem;font-weight:700;color:{col};letter-spacing:0.06em;">'
                f'{html_mod.escape(sev)}</span>'
                f'<span style="font-size:0.8rem;color:var(--text-primary);">'
                f'{html_mod.escape(f.get("title", ""))}</span>'
                f'<span style="margin-left:auto;font-size:0.67rem;color:var(--text-muted);'
                f'font-family:monospace;">{html_mod.escape(f.get("location", ""))}</span>'
                f'</summary>'
                f'<div style="padding:0.6rem 0.75rem 0.6rem 2rem;font-size:0.78rem;'
                f'color:var(--text-muted);line-height:1.5;">'
                f'<div style="margin-bottom:0.25rem;">'
                f'<code style="font-size:0.72rem;color:var(--accent-purple);">'
                f'{html_mod.escape(f.get("rule_id", ""))}</code></div>'
                f'{html_mod.escape(f.get("description", ""))}'
                f'</div></details>'
            )
        scanner_html += (
            f'<div style="margin-bottom:1.5rem;">'
            f'<h4 style="font-size:0.78rem;font-weight:600;letter-spacing:0.08em;'
            f'color:var(--text-muted);text-transform:uppercase;margin-bottom:0.6rem;">'
            f'{html_mod.escape(scanner_name)}</h4>'
            f'{rows}</div>'
        )

    total = len(all_findings)
    s = "s" if total != 1 else ""
    sc = "s" if len(scanners) != 1 else ""
    return (
        f'<section class="report-section">'
        f'<h2 class="section-title">SECURITY SCAN RESULTS</h2>'
        f'<p class="traceability-hint">{total} finding{s} across {len(scanners)} scanner{sc}. '
        f'Click &#9654; to see details.</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:1.5rem;">{badges}</div>'
        f'{scanner_html}'
        f'</section>'
    )


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Silverline release note artifacts."
    )
    parser.add_argument("--bdd-xml", type=Path, help="Path to BDD JUnit XML")
    parser.add_argument("--backend-xml", type=Path, help="Path to Django JUnit XML")
    parser.add_argument(
        "--features-dir", type=Path, help="Path to .feature files directory"
    )
    parser.add_argument(
        "--coverage-json", type=Path, help="Path to vitest coverage-summary.json"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("release"), help="Output directory"
    )
    parser.add_argument("--owner", default="Silverline-Software", help="Repo owner")
    parser.add_argument("--repo", default="real-random-portal", help="Repo name")
    parser.add_argument("--release-tag", default="dev", help="Release tag")
    parser.add_argument("--commit", default="unknown", help="Commit SHA")
    parser.add_argument("--run-url", default="", help="CI pipeline run URL")
    parser.add_argument("--security-bandit", default=None,
        help="Path to bandit JSON output file (bandit -f json -o ...)")
    parser.add_argument("--security-semgrep", default=None,
        help="Path to semgrep JSON output file (semgrep --json --output ...)")

    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Silverline Release Notes Generator v{SCHEMA_VERSION}")
    print(f"  Output: {args.output_dir}/")

    # Parse available inputs
    bdd_results = None
    backend_results = None
    features = None
    coverage_data = None

    junit = JUnitParser()

    if args.bdd_xml and args.bdd_xml.exists():
        print(f"  Parsing BDD XML: {args.bdd_xml}")
        bdd_results = junit.parse(args.bdd_xml)
        print(f"    {bdd_results['total']} tests found")
    elif args.bdd_xml:
        print(f"  BDD XML not found: {args.bdd_xml} (skipping)")

    if args.backend_xml and args.backend_xml.exists():
        print(f"  Parsing backend XML: {args.backend_xml}")
        backend_results = junit.parse(args.backend_xml)
        print(f"    {backend_results['total']} tests found")
    elif args.backend_xml:
        print(f"  Backend XML not found: {args.backend_xml} (skipping)")

    if args.features_dir and args.features_dir.is_dir():
        print(f"  Parsing features: {args.features_dir}")
        gherkin = GherkinParser()
        features = gherkin.parse_dir(args.features_dir)
        total_scenarios = sum(len(f["scenarios"]) for f in features)
        print(f"    {len(features)} files, {total_scenarios} scenarios")
    elif args.features_dir:
        print(f"  Features dir not found: {args.features_dir} (skipping)")

    if args.coverage_json and args.coverage_json.exists():
        print(f"  Parsing coverage: {args.coverage_json}")
        coverage_data = json.loads(args.coverage_json.read_text())
    elif args.coverage_json:
        print(f"  Coverage JSON not found: {args.coverage_json} (skipping)")

    # Collect security findings
    security_findings = []
    if args.security_bandit and os.path.exists(args.security_bandit):
        security_findings += parse_bandit_json(args.security_bandit)
    if args.security_semgrep and os.path.exists(args.security_semgrep):
        security_findings += parse_semgrep_json(args.security_semgrep)
    security_html = render_security_section(security_findings)

    # Build reports
    builder = ReportBuilder(
        owner=args.owner,
        repo=args.repo,
        release_tag=args.release_tag,
        commit_sha=args.commit,
        run_url=args.run_url,
    )

    # Executive report (always generated)
    print("\n  Generating executive-report.json...")
    executive = builder.build_executive_report(bdd_results, backend_results, features)
    _write_json(args.output_dir / "executive-report.json", executive)

    # Executive HTML report
    print("  Generating executive-report.html...")
    html_out = builder.build_executive_html(executive, features)
    if security_html:
        html_out = html_out.replace("</main>", security_html + "\n    </main>", 1)
    (args.output_dir / "executive-report.html").write_text(html_out)

    # Unit test summary (only if backend results exist)
    if backend_results:
        print("  Generating unit-test-summary.json...")
        unit_summary = builder.build_unit_test_summary(backend_results)
        _write_json(args.output_dir / "unit-test-summary.json", unit_summary)

    # Coverage summary (only if coverage data exists)
    if coverage_data:
        print("  Generating coverage-summary.json...")
        cov_summary = builder.build_coverage_summary(coverage_data)
        _write_json(args.output_dir / "coverage-summary.json", cov_summary)

    print(f"\nDone. Reports written to {args.output_dir}/")
    return 0


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    sys.exit(main())
