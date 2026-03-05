Feature: Schema Validation

  @req-SCHEMA-01
  Scenario: Valid report passes schema validation
    Given a structurally complete executive report
    When I validate the report against the schema
    Then no validation errors are returned

  @req-SCHEMA-02
  Scenario: Report missing a required key fails validation
    Given an executive report with the summary field removed
    When I validate the report against the schema
    Then a validation error mentioning "summary" is returned

  @req-SCHEMA-03
  Scenario: Integer pass_rate is accepted where float is expected
    Given a structurally complete executive report with an integer pass_rate
    When I validate the report against the schema
    Then no validation errors are returned
