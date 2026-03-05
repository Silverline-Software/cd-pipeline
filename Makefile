
.DEFAULT_GOAL := help

CLAUDE_FLAGS := --allow-dangerously-skip-permissions
PYTHON       := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)

# ── Variables ─────────────────────────────────────────────────────────────────

OUTPUT_DIR   ?= release
FEATURES_DIR ?= test/acceptance/features
BDD_XML      ?= test-results/results.xml
BACKEND_XML  ?= test-results/backend-results.xml
RELEASE_TAG  ?= local-v0.0.0
OWNER        ?= Silverline-Software
REPO         ?= $(shell basename $(shell git rev-parse --show-toplevel) 2>/dev/null || echo unknown)
COMMIT       ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)

# ── Help ──────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@echo "Silverline Release Documentation"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Report Generation:"
	@grep -E '^(generate|validate|lint|check|clean|test).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-28s %s\n", $$1, $$2}'
	@echo ""
	@echo "Claude Code:"
	@grep -E '^claude.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-28s %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables (override with VAR=value):"
	@echo "  OUTPUT_DIR=$(OUTPUT_DIR)"
	@echo "  RELEASE_TAG=$(RELEASE_TAG)"
	@echo "  OWNER=$(OWNER)"
	@echo "  REPO=$(REPO)"

# ── Report Generation ─────────────────────────────────────────────────────────

.PHONY: generate
generate: ## Generate release notes from test results (use OUTPUT_DIR, BDD_XML, BACKEND_XML, RELEASE_TAG)
	$(PYTHON) scripts/generate_release_notes.py \
		$(if $(wildcard $(BDD_XML)),--bdd-xml $(BDD_XML)) \
		$(if $(wildcard $(BACKEND_XML)),--backend-xml $(BACKEND_XML)) \
		$(if $(wildcard $(FEATURES_DIR)),--features-dir $(FEATURES_DIR)) \
		--output-dir $(OUTPUT_DIR) \
		--owner $(OWNER) \
		--repo $(REPO) \
		--release-tag "$(RELEASE_TAG)" \
		--commit "$(COMMIT)"
	@echo ""
	@echo "Reports written to $(OUTPUT_DIR)/"

.PHONY: generate-example
generate-example: ## Generate a sample report using the example requirements manifest
	@mkdir -p $(OUTPUT_DIR)
	PYTHONPATH=examples $(PYTHON) scripts/generate_release_notes.py \
		--output-dir $(OUTPUT_DIR) \
		--owner $(OWNER) \
		--repo $(REPO) \
		--release-tag "$(RELEASE_TAG)" \
		--commit "$(COMMIT)"
	@echo ""
	@echo "Example report written to $(OUTPUT_DIR)/"

.PHONY: validate
validate: ## Validate the requirements_manifest.py in scripts/ (syntax + structure check)
	@if [ -f scripts/requirements_manifest.py ]; then \
		$(PYTHON) -c "import sys; sys.path.insert(0,'scripts'); from requirements_manifest import CATEGORIES, PHASES, REQUIREMENTS, normalize_tag; print('manifest OK — categories:', len(CATEGORIES), '| phases:', len(PHASES), '| requirements:', len(REQUIREMENTS))"; \
	else \
		echo "No scripts/requirements_manifest.py found — copy from examples/ to get started"; \
		exit 1; \
	fi

.PHONY: lint
lint: ## Lint Python scripts with ruff (falls back to flake8, then pyflakes)
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check scripts/; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 scripts/ --max-line-length=120; \
	elif command -v pyflakes >/dev/null 2>&1; then \
		pyflakes scripts/; \
	else \
		echo "No linter found — install ruff: pip install ruff"; \
	fi

.PHONY: check
check: validate lint ## Run all checks (validate manifest + lint)

.PHONY: test
test: ## Run all tests — unit + acceptance (requires: pip install pytest pytest-bdd)
	$(PYTHON) -m pytest test/ -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTHON) -m pytest test/unit/ -v

.PHONY: test-acceptance
test-acceptance: ## Run acceptance tests only (requires pytest-bdd)
	$(PYTHON) -m pytest test/acceptance/ -v

.PHONY: clean
clean: ## Remove generated report files
	rm -rf $(OUTPUT_DIR)
	@echo "Cleaned $(OUTPUT_DIR)/"

# ── Claude Code ───────────────────────────────────────────────────────────────

.PHONY: claude
claude: ## Open Claude Code (interactive, skip permissions)
	claude $(CLAUDE_FLAGS)

.PHONY: claude-opus
claude-opus: ## Open Claude Code with Opus model
	claude --model opus $(CLAUDE_FLAGS)

.PHONY: claude-sonnet
claude-sonnet: ## Open Claude Code with Sonnet model
	claude --model sonnet $(CLAUDE_FLAGS)

.PHONY: claude-resume
claude-resume: ## Resume the last Claude Code session
	claude -r $(CLAUDE_FLAGS)

.PHONY: claude-continue
claude-continue: ## Continue the last Claude Code conversation
	claude -c $(CLAUDE_FLAGS)

.PHONY: claude-plan
claude-plan: ## Open Claude Code in plan mode (review before executing)
	claude --plan $(CLAUDE_FLAGS)
