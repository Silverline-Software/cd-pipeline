Feature: Report Generation

  @req-GEN-01 @req-GEN-02
  Scenario: Generator produces output files with no test inputs
    Given the report generator script is available
    When I run the generator with a release tag and an output directory
    Then executive-report.json is created in the output directory
    And executive-report.html is created in the output directory

  @req-GEN-03
  Scenario: Generated JSON contains the supplied release tag
    Given the report generator script is available
    When I run the generator with release tag "acc-v3.1.0"
    Then the executive-report.json release_tag equals "acc-v3.1.0"

  @req-GEN-04
  Scenario: Generated JSON conforms to the executive report schema
    Given the report generator script is available
    When I run the generator with a release tag and an output directory
    Then the executive-report.json passes schema validation
