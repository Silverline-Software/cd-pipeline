Feature: Gherkin Parsing

  @req-PARSE-01
  Scenario: Parser extracts scenario names from a feature file
    Given a feature file containing two scenarios
    When I parse the feature directory
    Then both scenario names appear in the parsed results

  @req-PARSE-02
  Scenario: Parser associates req tags with scenarios
    Given a feature file containing two scenarios
    When I parse the feature directory
    Then the req_tags include "req-AUTH-01"
    And the req_tags include "FR-AUTH-02"

  @req-PARSE-03
  Scenario: Parser extracts Gherkin step keywords
    Given a feature file containing two scenarios
    When I parse the feature directory
    Then the steps contain the Given When and Then keywords
