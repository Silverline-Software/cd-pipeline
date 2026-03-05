# Release Documentation Tool — Functional Requirements

## REQ-GEN: Report Generation

| ID | Description | Priority |
|----|-------------|----------|
| REQ-GEN-01 | Invoking the report generator with no test inputs produces `executive-report.json` | P0 |
| REQ-GEN-02 | Invoking the report generator with no test inputs produces `executive-report.html` | P0 |
| REQ-GEN-03 | Generated JSON report contains the release tag supplied as input | P0 |
| REQ-GEN-04 | Generated JSON report conforms to the executive report schema | P0 |

## REQ-SCHEMA: Schema Validation

| ID | Description | Priority |
|----|-------------|----------|
| REQ-SCHEMA-01 | `validate_report` returns no errors for a structurally valid report | P0 |
| REQ-SCHEMA-02 | `validate_report` returns errors for a report missing required keys | P0 |
| REQ-SCHEMA-03 | `validate_report` accepts integer values where float is expected | P1 |

## REQ-PARSE: Gherkin & JUnit Parsing

| ID | Description | Priority |
|----|-------------|----------|
| REQ-PARSE-01 | `GherkinParser` extracts scenario names from `.feature` files | P0 |
| REQ-PARSE-02 | `GherkinParser` associates `@req-*` and `@FR-*` tags with their scenarios | P0 |
| REQ-PARSE-03 | `GherkinParser` extracts Given/When/Then steps for each scenario | P1 |
| REQ-PARSE-04 | `JUnitParser` extracts pass/fail totals from JUnit XML | P0 |
| REQ-PARSE-05 | `JUnitParser.scenario_to_test_name` converts scenario names to pytest function names | P1 |

## REQ-MAKE: Makefile Targets

| ID | Description | Priority |
|----|-------------|----------|
| REQ-MAKE-01 | `make generate-example` produces `executive-report.json` and `executive-report.html` | P0 |
| REQ-MAKE-02 | `make validate` exits 0 when a valid `requirements_manifest.py` is present in `scripts/` | P0 |
| REQ-MAKE-03 | `make lint` exits 0 on the project scripts | P1 |

## Traceability

| Requirement | Acceptance Scenario Tag | Unit Test |
|-------------|------------------------|-----------|
| REQ-GEN-01  | `@req-GEN-01` | `test_report_builder.py::test_executive_report_without_inputs` |
| REQ-GEN-02  | `@req-GEN-02` | `test_report_builder.py::test_executive_report_without_inputs` |
| REQ-GEN-03  | `@req-GEN-03` | `test_report_builder.py::test_executive_report_contains_release_tag` |
| REQ-GEN-04  | `@req-GEN-04` | `test_report_builder.py::test_executive_report_conforms_to_schema` |
| REQ-SCHEMA-01 | `@req-SCHEMA-01` | `test_schema.py::test_valid_report_has_no_errors` |
| REQ-SCHEMA-02 | `@req-SCHEMA-02` | `test_schema.py::test_missing_key_reported_as_error` |
| REQ-SCHEMA-03 | `@req-SCHEMA-03` | `test_schema.py::test_int_accepted_where_float_expected` |
| REQ-PARSE-01 | `@req-PARSE-01` | `test_gherkin_parser.py::test_parser_extracts_scenario_names` |
| REQ-PARSE-02 | `@req-PARSE-02` | `test_gherkin_parser.py::test_parser_extracts_req_tags` |
| REQ-PARSE-03 | `@req-PARSE-03` | `test_gherkin_parser.py::test_parser_extracts_steps` |
| REQ-PARSE-04 | `@req-PARSE-04` | `test_junit_parser.py::test_junit_parser_extracts_results` |
| REQ-PARSE-05 | `@req-PARSE-05` | `test_junit_parser.py::test_junit_parser_scenario_name_mapping` |
| REQ-MAKE-01 | `@req-MAKE-01` | — (integration only) |
| REQ-MAKE-02 | `@req-MAKE-02` | — (integration only) |
| REQ-MAKE-03 | `@req-MAKE-03` | — (integration only) |
