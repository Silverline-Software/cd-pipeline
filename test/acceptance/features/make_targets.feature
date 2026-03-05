Feature: Makefile Targets

  Background:
    Given the project Makefile is present

  @req-MAKE-01
  Scenario: make generate-example produces output files
    When I run make generate-example with a temporary output directory
    Then executive-report.json exists in the output directory
    And executive-report.html exists in the output directory

  @req-MAKE-02
  Scenario: make validate passes with a valid manifest
    Given a requirements manifest is installed in scripts
    When I run make validate
    Then the make command exits with code 0

  @req-MAKE-03
  Scenario: make lint passes on project scripts
    When I run make lint
    Then the make command exits with code 0
