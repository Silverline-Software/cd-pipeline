Feature: CI/CD Deployment Gate

  Official releases are only deployed through the Silverline CD Pipeline when
  all CI checks for the release commit have completed successfully. This prevents
  broken or untested builds from reaching Firebase Hosting.

  @req-CICD-001
  Scenario: Deployment proceeds when all CI checks pass
    Given the CI gate script is available
    And a mock GitHub API reporting 2 successful check runs
    When I run the CI gate for repo "Silverline-Software/cd-pipeline" commit "abc1234"
    Then the gate exits with code 0
    And the output contains "CI gate passed"

  @req-CICD-001
  Scenario: Deployment is blocked when a CI check has failed
    Given the CI gate script is available
    And a mock GitHub API reporting 1 failed and 1 successful check run
    When I run the CI gate for repo "Silverline-Software/cd-pipeline" commit "abc1234"
    Then the gate exits with a non-zero code
    And the output contains "failed"

  @req-CICD-002
  Scenario: Deployment is blocked when a CI check is still in progress
    Given the CI gate script is available
    And a mock GitHub API reporting 1 in-progress check run
    When I run the CI gate for repo "Silverline-Software/cd-pipeline" commit "abc1234"
    Then the gate exits with a non-zero code
    And the output contains "in progress"

  @req-CICD-003
  Scenario: Deployment is blocked when no CI checks exist for the commit
    Given the CI gate script is available
    And a mock GitHub API reporting no check runs
    When I run the CI gate for repo "Silverline-Software/cd-pipeline" commit "abc1234"
    Then the gate exits with a non-zero code
    And the output contains "No CI checks found"
