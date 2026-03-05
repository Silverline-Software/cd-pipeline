# Silverline Release Documentation

Reusable infrastructure for generating branded **Silverline Release Notes** from test results and deploying them to Firebase Hosting with versioned URLs.

Each release gets a permanent URL. Reports show requirement coverage with expandable Gherkin scenarios, pass/fail status indicators, and a version switcher for navigating between releases.

---

## How It Works

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│  CI Pipeline  │───▶│  Report Generator │───▶│  GitHub Release      │
│  (tests run)  │    │  (JSON + HTML)    │    │  (assets attached)   │
└──────────────┘    └──────────────────┘    └──────────┬───────────┘
                                                        │
                                                        ▼
                                            ┌──────────────────────┐
                                            │  CD Pipeline         │
                                            │  (Firebase Hosting)  │
                                            └──────────┬───────────┘
                                                        │
                                                        ▼
                                            ┌──────────────────────┐
                                            │  Versioned URLs      │
                                            │  /<env>/<version>/   │
                                            └──────────────────────┘
```

---

## Tag Convention

The **release tag** encodes both the environment and version:

```
<env_name>-v<X.Y.Z>[-rc]
```

| Tag | Environment | Version | RC? | URL Path |
|-----|------------|---------|-----|----------|
| `pre-release-registry-v0.1.0-rc` | `pre-release-registry` | `v0.1.0` | yes | `/pre-release-registry/v0.1.0/rc` |
| `pre-release-registry-v0.1.0` | `pre-release-registry` | `v0.1.0` | no | `/pre-release-registry/v0.1.0/` |
| `release-v1.0.0` | `release` | `v1.0.0` | no | `/release/v1.0.0/` |
| `staging-v2.0.0-rc` | `staging` | `v2.0.0` | yes | `/staging/v2.0.0/rc` |
| `v1.0.0` (bare) | `release` | `v1.0.0` | no | `/release/v1.0.0/` |

Bare tags (no prefix) fall back to the `DEFAULT_ENV` variable (defaults to `release`).

---

## Quick Start — Add to an Existing Project

### Step 1: Copy the scripts

```bash
# From your project root
mkdir -p scripts
cp <this-repo>/scripts/generate_release_notes.py scripts/
cp <this-repo>/scripts/release_notes_schema.py scripts/
cp <this-repo>/examples/requirements_manifest.py scripts/requirements_manifest.py
```

### Step 2: Customize the requirements manifest

Edit `scripts/requirements_manifest.py`:
- Define your **PHASES** (delivery milestones)
- Define your **CATEGORIES** (functional areas matching your tag prefixes)
- Add your **REQUIREMENTS** with description, priority, and status
- Update `normalize_tag()` if your project uses a different tag prefix

### Step 3: Tag your Gherkin scenarios

In your `.feature` files, tag scenarios with requirement IDs:

```gherkin
@req-AUTH-01 @story-1-1
Scenario: User registers with valid credentials
  Given the user is on the registration page
  When they submit valid registration details
  Then their account is created
```

Both `@req-<ID>` and `@FR-<ID>` prefixes are supported out of the box.

### Step 4: Add report generation to CI

Add a job to your CI workflow that runs after tests:

```yaml
generate-reports:
  name: Generate Functionality Reports
  runs-on: ubuntu-latest
  needs: [test, backend-test]  # your test jobs
  if: always()

  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Download test results
      uses: actions/download-artifact@v4
      continue-on-error: true
      with:
        name: test-results
        path: test-results/

    - name: Generate reports
      env:
        REF_NAME: ${{ github.ref_name }}
        COMMIT_SHA: ${{ github.sha }}
        SERVER_URL: ${{ github.server_url }}
        REPO: ${{ github.repository }}
        RUN_ID: ${{ github.run_id }}
      run: |
        python scripts/generate_release_notes.py \
          --bdd-xml test-results/results.xml \
          --backend-xml test-results/backend-results.xml \
          --features-dir test/acceptance/features/ \
          --output-dir release/ \
          --owner <your-org> \
          --repo <your-repo> \
          --release-tag "$REF_NAME" \
          --commit "$COMMIT_SHA" \
          --run-url "${SERVER_URL}/${REPO}/actions/runs/${RUN_ID}"

    - name: Upload reports
      uses: actions/upload-artifact@v4
      with:
        name: silverline-release-notes
        path: release/
        retention-days: 90
```

### Step 5: Attach reports to releases

In your release workflow, download the reports artifact and include the files:

```yaml
- name: Download reports
  uses: actions/download-artifact@v4
  with:
    name: silverline-release-notes
    path: release/

- name: Create release
  uses: softprops/action-gh-release@v2
  with:
    files: |
      release/executive-report.json
      release/executive-report.html
      release/unit-test-summary.json
      release/coverage-summary.json
```

### Step 6: Copy the CD workflow

```bash
cp <this-repo>/.github/workflows/silverline-release-notes-cd.yml \
   .github/workflows/silverline-release-notes-cd.yml
```

### Step 7: Set up Firebase Hosting (one-time)

See [Firebase Hosting Setup](#firebase-hosting-setup) below.

### Step 8: Create a release

Tag and release using the standard format:

```bash
git tag pre-release-registry-v0.1.0-rc
git push origin pre-release-registry-v0.1.0-rc
# Then create a GitHub release from the tag
```

The CD workflow triggers automatically on release publish.

---

## Firebase Hosting Setup

### One-time: Create the Firebase project

1. Go to [Firebase Console](https://console.firebase.google.com/) and create a new project (or use an existing one like `silverline-release-hub`)
2. Enable **Hosting** in the Firebase console

### One-time: Create a GCP service account

```bash
# Authenticate with the Google account that owns the Firebase project
gcloud auth login

# Create service account
gcloud iam service-accounts create github-deploy \
  --display-name="GitHub Actions Deploy" \
  --project=<FIREBASE_PROJECT_ID>

# Grant Firebase Hosting admin role
gcloud projects add-iam-policy-binding <FIREBASE_PROJECT_ID> \
  --member="serviceAccount:github-deploy@<FIREBASE_PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/firebasehosting.admin"

# Generate JSON key
gcloud iam service-accounts keys create /tmp/firebase-sa-key.json \
  --iam-account="github-deploy@<FIREBASE_PROJECT_ID>.iam.gserviceaccount.com"
```

### Store the service account key

**Organization-level secret** (recommended — reusable across repos):
```bash
# Requires admin:org scope
gh secret set RELEASE_NOTES_GCP_SA_KEY \
  --org <your-org> \
  --body "$(cat /tmp/firebase-sa-key.json)"
```

Or add it manually in GitHub: **Organization Settings > Secrets and variables > Actions > New organization secret**

**Clean up the local key file:**
```bash
rm /tmp/firebase-sa-key.json
```

### Per-repo: Create the GitHub environment

```bash
# Create the environment
gh api repos/<org>/<repo>/environments/release-notes-hosting -X PUT

# Set environment variables
gh api repos/<org>/<repo>/environments/release-notes-hosting/variables \
  -X POST -f name=FIREBASE_PROJECT_ID -f value=<your-firebase-project-id>

gh api repos/<org>/<repo>/environments/release-notes-hosting/variables \
  -X POST -f name=PROJECT_DISPLAY_NAME -f value="My Project — Release Reports"
```

That's it. The CD workflow reads `FIREBASE_PROJECT_ID` from the environment and `RELEASE_NOTES_GCP_SA_KEY` from org secrets.

### Optional: Custom domain

To use a custom domain like `myapp.releases.yourdomain.com`:

1. In Firebase Console > Hosting > Add custom domain
2. Add the DNS records Firebase provides (typically a TXT record for verification, then an A record)
3. Wait for SSL provisioning (usually a few minutes)

---

## Granting Access from External Services (AWS EC2, etc.)

If you need an external service (like an AWS EC2 instance) to access the hosted reports, there are several approaches:

### Option A: Public Firebase Hosting (default)

Firebase Hosting sites are public by default. If your reports don't contain sensitive information, no additional configuration is needed. Any service can fetch the reports via HTTPS:

```bash
# From an EC2 instance or any server
curl https://<firebase-project>.web.app/pre-release-registry/v0.1.0/

# Fetch the JSON report programmatically
curl -s https://<firebase-project>.web.app/pre-release-registry/v0.1.0/executive-report.json | jq .
```

### Option B: Restrict access with Firebase Auth + Cloud Functions

If reports contain sensitive data:

1. Set up Firebase Authentication
2. Create a Cloud Function that verifies auth tokens before serving content
3. Issue service account tokens for EC2 access

### Option C: Access release assets directly from GitHub

EC2 instances can fetch report artifacts directly from GitHub releases (useful if you don't want Firebase at all):

```bash
# Using GitHub CLI (install: https://cli.github.com/)
gh release download <tag> \
  -R <org>/<repo> \
  -p "executive-report.html" \
  -D /tmp/reports/

# Using the GitHub API with a token
curl -L \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/octet-stream" \
  "https://api.github.com/repos/<org>/<repo>/releases/assets/<asset_id>" \
  -o report.html
```

**To set up GitHub CLI on an EC2 instance:**

```bash
# Install gh CLI
sudo apt-get update && sudo apt-get install -y gh

# Authenticate (use a Personal Access Token with repo scope)
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Or use a GitHub App installation token for production
```

### Option D: AWS-specific integration

For AWS services that need to consume report data:

1. **S3 sync**: Add a step to your CD workflow that also uploads reports to an S3 bucket
2. **CloudFront**: Put CloudFront in front of Firebase Hosting for AWS-native caching
3. **Lambda**: Use a Lambda function to fetch and cache reports from Firebase/GitHub

---

## Report Generator CLI Reference

```
python scripts/generate_release_notes.py [OPTIONS]
```

| Flag | Description | Default |
|------|-------------|---------|
| `--bdd-xml PATH` | JUnit XML from BDD acceptance tests | (none) |
| `--backend-xml PATH` | JUnit XML from backend unit tests | (none) |
| `--features-dir PATH` | Directory containing `.feature` files | (none) |
| `--coverage-json PATH` | Vitest `coverage-summary.json` | (none) |
| `--output-dir PATH` | Output directory for reports | `release/` |
| `--owner TEXT` | GitHub org/owner name | (none) |
| `--repo TEXT` | GitHub repo name | (none) |
| `--release-tag TEXT` | Release tag (e.g., `v1.0.0`) | (none) |
| `--commit TEXT` | Git commit SHA | (none) |
| `--run-url TEXT` | URL to the CI pipeline run | (none) |

All flags are optional. The script produces partial reports when inputs are missing.

### Output files

| File | Required? | Description |
|------|-----------|-------------|
| `executive-report.json` | Yes | Structured report with requirement coverage |
| `executive-report.html` | Yes | Branded HTML report with expandable scenarios |
| `unit-test-summary.json` | No | Backend test results (if `--backend-xml` provided) |
| `coverage-summary.json` | No | Code coverage data (if `--coverage-json` provided) |

---

## Status Indicators

The HTML report shows these indicators for each requirement:

| Symbol | CSS Class | Meaning |
|--------|-----------|---------|
| ✓ | `--passing` | All tagged scenarios pass |
| ✗ | `--failing` | One or more scenarios fail |
| ~ | `--partial` | Mixed pass/fail results |
| — | `--untested` | No test scenarios tagged for this requirement |

---

## Environment Variables Reference

### Organization secret (shared across repos)

| Secret | Description |
|--------|-------------|
| `RELEASE_NOTES_GCP_SA_KEY` | GCP service account JSON key for Firebase deploy |

### Per-repo environment variables (in `release-notes-hosting` environment)

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID for deployment |
| `PROJECT_DISPLAY_NAME` | No | Display name on the versions index page (default: `Release Reports`) |
| `DEFAULT_ENV` | No | Fallback environment for bare tags like `v1.0.0` (default: `release`) |

---

## Customizing Tag Prefixes

The report generator supports both `@req-<TYPE>-<NUM>` and `@FR-<TYPE>-<NUM>` out of the box.

To add a custom prefix, update `normalize_tag()` in your project's `requirements_manifest.py`:

```python
def normalize_tag(tag: str) -> str:
    """Strip tag prefix to get normalized requirement ID."""
    for prefix in ("req-", "FR-", "REQ-", "US-"):  # add your prefixes
        if tag.startswith(prefix):
            return tag[len(prefix):]
    return tag
```

---

## Directory Structure

```
silverline-software/release-documentation/
├── README.md                           # This file
├── scripts/
│   ├── generate_release_notes.py      # Report generator (copy to your project)
│   └── release_notes_schema.py       # JSON schema definitions
├── .github/
│   └── workflows/
│       └── silverline-release-notes-cd.yml  # CD workflow (copy to your project)
└── examples/
    ├── requirements_manifest.py        # Minimal template to customize
    └── requirements_manifest_real_random.py  # Full real-world example
```

---

## Adding to a New Project — Checklist

- [ ] Copy `scripts/generate_release_notes.py` and `scripts/release_notes_schema.py`
- [ ] Create `scripts/requirements_manifest.py` (start from template)
- [ ] Tag Gherkin scenarios with `@req-<TYPE>-<NUM>` or `@FR-<TYPE>-<NUM>`
- [ ] Add `generate-reports` job to CI workflow
- [ ] Attach report files to GitHub releases
- [ ] Copy `silverline-release-notes-cd.yml` to `.github/workflows/`
- [ ] Create `release-notes-hosting` GitHub environment
- [ ] Set `FIREBASE_PROJECT_ID` environment variable
- [ ] Set `PROJECT_DISPLAY_NAME` environment variable (optional)
- [ ] Ensure `RELEASE_NOTES_GCP_SA_KEY` org secret is accessible to the repo
- [ ] Create a release with the standard tag format and verify deployment
