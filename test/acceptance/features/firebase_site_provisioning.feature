Feature: Firebase Site Provisioning

  The CD pipeline must ensure the Firebase Hosting site exists before deploying.
  The provisioning script is idempotent — safe to run on every deploy regardless
  of whether the site was previously created.

  @req-SITE-01
  Scenario: Site is created when it does not exist
    Given the Firebase site provisioning script is available
    And a mock firebase that successfully creates the site
    When I run the provisioning script for project "test-project" site "new-site"
    Then the script exits with code 0
    And the output contains "Created Firebase Hosting site"

  @req-SITE-02
  Scenario: Script is idempotent when site already exists
    Given the Firebase site provisioning script is available
    And a mock firebase that reports the site already exists
    When I run the provisioning script for project "test-project" site "existing-site"
    Then the script exits with code 0
    And the output contains "already exists"

  @req-SITE-03
  Scenario: Script fails loudly on unexpected Firebase errors
    Given the Firebase site provisioning script is available
    And a mock firebase that reports an authentication error
    When I run the provisioning script for project "test-project" site "any-site"
    Then the script exits with a non-zero code
