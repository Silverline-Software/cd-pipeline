# Example Requirements Manifests

Templates a consumer project copies to `scripts/requirements_manifest.py` and
customizes.

| File | Purpose |
|------|---------|
| `requirements_manifest.py` | Minimal template — phases, categories, and a few requirements using the per-requirement `Phase` enum. |
| `requirements_manifest_real_random.py` | A fuller real-world example. |

Each requirement entry is `(description, priority, status, Phase)` where `Phase`
is `silverline.reporting.phases.Phase` (`MVP`, `PHASE_1` … `PHASE_10`). The
legacy 3-tuple form (phase inherited from the category) is still supported.

---
Copyright © 2026 Silverline Software LLC. All Rights Reserved.
