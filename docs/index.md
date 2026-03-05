# Silverline CD Pipeline

**Automated release documentation and deployment for Silverline Software projects.**

The Silverline CD Pipeline toolkit orchestrates the full lifecycle of a software release:

1. **CI gate** — verifies all checks passed before deployment is allowed
2. **Report generation** — produces branded HTML release notes from test results
3. **Docs deployment** — publishes API docs to `/docs/` on the release site
4. **Firebase Hosting** — deploys versioned reports to a per-project subdomain

---

## Package structure

```
silverline/
├── pipeline/
│   ├── release.py    ReleaseTag, Release
│   ├── gates.py      CIGate, GateResult, CheckRun
│   └── deploy.py     DeploymentPipeline, DeployResult
└── hosting/
    ├── site.py       HostingSite, CacheRule
    └── firebase.py   FirebaseClient, FirebaseError
```

## Quick start

```python
from silverline import DeploymentPipeline

pipeline = DeploymentPipeline(
    repo="Silverline-Software/my-project",
    firebase_project="silverline-release-hub",
    site_id="my-project",
)

result = pipeline.run("release-v1.2.0")
if not result.success:
    raise SystemExit(result.error)

print(f"Deployed {result.deployed_versions} version(s) → {result.hosting_url}")
```

## Tag convention

| Tag | Environment | Version | RC? | URL path |
|-----|-------------|---------|-----|----------|
| `release-v1.0.0` | release | 1.0.0 | No | `/release/v1.0.0/` |
| `staging-v0.9.1-rc` | staging | 0.9.1 | Yes | `/staging/v0.9.1/rc/` |
| `v2.0.0` | release *(default)* | 2.0.0 | No | `/release/v2.0.0/` |

## CI gate

Every deployment is gated on CI. The [`CIGate`][silverline.pipeline.gates.CIGate]
queries the GitHub Checks API for the release commit and blocks deployment if
any check is pending or failed.

```python
from silverline.pipeline.gates import CIGate

gate = CIGate("Silverline-Software/my-project")
result = gate.evaluate("abc1234")

print(result.status)        # GateStatus.PASSED
print(len(result.failures)) # 0
```
