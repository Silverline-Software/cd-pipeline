# Requirements Traceability Matrix — Silverline CD Pipeline

**Project:** Silverline Software CD Pipeline
**Version:** v1.0.0

---

## GEN — Report Generation

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| GEN-01 | Generator produces `executive-report.json` with no test inputs | P0 | Implemented | `@req-GEN-01` | `test_report_builder.py::test_executive_report_without_inputs` |
| GEN-02 | Generator produces `executive-report.html` with no test inputs | P0 | Implemented | `@req-GEN-02` | `test_report_builder.py::test_executive_report_without_inputs` |
| GEN-03 | Generated JSON report contains the supplied release tag | P0 | Implemented | `@req-GEN-03` | `test_report_builder.py::test_executive_report_contains_release_tag` |
| GEN-04 | Generated JSON report conforms to the executive report schema | P0 | Implemented | `@req-GEN-04` | `test_report_builder.py::test_executive_report_conforms_to_schema` |

## SCHEMA — Schema Validation

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| SCHEMA-01 | `validate_report` returns no errors for a structurally valid report | P0 | Implemented | `@req-SCHEMA-01` | `test_schema.py::test_valid_report_has_no_errors` |
| SCHEMA-02 | `validate_report` reports errors for a report missing required keys | P0 | Implemented | `@req-SCHEMA-02` | `test_schema.py::test_missing_key_reported_as_error` |
| SCHEMA-03 | `validate_report` accepts integer values where float is expected | P1 | Implemented | `@req-SCHEMA-03` | `test_schema.py::test_int_accepted_where_float_expected` |

## PARSE — Gherkin & JUnit Parsing

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| PARSE-01 | `GherkinParser` extracts scenario names from `.feature` files | P0 | Implemented | `@req-PARSE-01` | `test_gherkin_parser.py::test_parser_extracts_scenario_names` |
| PARSE-02 | `GherkinParser` associates `@req-*` and `@FR-*` tags with scenarios | P0 | Implemented | `@req-PARSE-02` | `test_gherkin_parser.py::test_parser_extracts_req_tags` |
| PARSE-03 | `GherkinParser` extracts Given/When/Then steps for each scenario | P1 | Implemented | `@req-PARSE-03` | `test_gherkin_parser.py::test_parser_extracts_steps` |
| PARSE-04 | `JUnitParser` extracts pass/fail totals from JUnit XML | P0 | Implemented | `@req-PARSE-04` | `test_junit_parser.py::test_junit_parser_extracts_results` |
| PARSE-05 | `JUnitParser` maps scenario names to pytest test function names | P1 | Implemented | `@req-PARSE-05` | `test_junit_parser.py::test_junit_parser_scenario_name_mapping` |

## MAKE — Makefile Targets

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| MAKE-01 | `make generate-example` produces report output files | P0 | Implemented | `@req-MAKE-01` | — (integration only) |
| MAKE-02 | `make validate` exits 0 when `requirements_manifest.py` is present | P0 | Implemented | `@req-MAKE-02` | — (integration only) |
| MAKE-03 | `make lint` exits 0 on project scripts | P1 | Implemented | `@req-MAKE-03` | — (integration only) |

## SITE — Firebase Site Provisioning

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| SITE-01 | CD pipeline creates the Firebase Hosting site if it does not exist | P0 | Implemented | `@req-SITE-01` | — (integration only) |
| SITE-02 | CD pipeline is idempotent — re-running when site exists does not fail | P0 | Implemented | `@req-SITE-02` | — (integration only) |
| SITE-03 | CD pipeline fails loudly on unexpected Firebase errors | P0 | Implemented | `@req-SITE-03` | — (integration only) |

## CICD — CI/CD Release Pipeline

| Req ID | Description | Priority | Status | Acceptance Tag | Unit Test |
|--------|-------------|----------|--------|----------------|-----------|
| CICD-001 | Official releases are only deployed when all CI checks have passed | P0 | Implemented | `@req-CICD-001` | — (integration only) |
| CICD-002 | Deployment is blocked when CI checks are still in progress | P0 | Implemented | `@req-CICD-002` | — (integration only) |
| CICD-003 | Deployment is blocked when no CI checks exist for the release commit | P0 | Implemented | `@req-CICD-003` | — (integration only) |

---

## Coverage Summary

| Category | Total Reqs | P0 | P1 | Implemented | With Acceptance Test | With Unit Test |
|----------|-----------|----|----|-------------|---------------------|---------------|
| GEN | 4 | 4 | 0 | 4 | 4 | 4 |
| SCHEMA | 3 | 2 | 1 | 3 | 3 | 3 |
| PARSE | 5 | 3 | 2 | 5 | 5 | 5 |
| MAKE | 3 | 2 | 1 | 3 | 3 | 0 |
| SITE | 3 | 3 | 0 | 3 | 3 | 0 |
| CICD | 3 | 3 | 0 | 3 | 3 | 0 |
| **Total** | **21** | **17** | **4** | **21** | **21** | **12** |
