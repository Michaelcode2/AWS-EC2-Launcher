# windows-distribution Specification

## Purpose
Produces a signed-capable Windows installer from GitHub Actions or a local Windows build, while Docker provides a reproducible local path for tests and non-GUI checks.
## Requirements
### Requirement: Standalone Windows application
The distributed application SHALL run on a clean Windows 10/11 x64 machine without requiring Python to be installed.

#### Scenario: Clean Windows install
- **WHEN** the installer is run on a supported Windows machine without Python
- **THEN** the application launches and presents the login/profile flow

### Requirement: Installer behavior
The installer SHALL place the application under Program Files, create shortcuts and an application icon, create a per-user configuration directory, optionally detect AWS CLI, register the product in Windows Apps, support uninstall, and MUST NOT write credentials into the installation directory.

#### Scenario: Fresh install directories
- **WHEN** installation completes
- **THEN** the program files contain the application and the per-user config directory exists without AWS secrets

#### Scenario: Uninstall
- **WHEN** the product is uninstalled
- **THEN** the application is removed from Windows Apps and Program Files

### Requirement: GitHub Actions Windows compile
A GitHub Actions workflow SHALL compile the Windows application and build the installer on a Windows runner, then publish the installer as a workflow artifact.

#### Scenario: Workflow on default branch
- **WHEN** the workflow runs on a configured branch or tag
- **THEN** it produces a Windows installer artifact without embedding secrets

### Requirement: Local Docker test path
A local Docker workflow SHALL run unit tests and linters for non-GUI logic so developers can verify behavior without a Windows machine.

#### Scenario: Docker test job
- **WHEN** a developer runs the documented Docker test command
- **THEN** unit tests and linters execute in the container and report pass or fail

### Requirement: No secrets in build artifacts
Build outputs MUST NOT include AWS keys, Windows passwords, signing private keys, or SSO tokens.

#### Scenario: Artifact inspection
- **WHEN** CI artifacts are produced
- **THEN** they contain no credentials or private keys

### Requirement: Optional Authenticode signing
When a signing certificate is available to CI, the workflow SHALL sign the executable and installer. When it is not available, the workflow SHALL still produce an unsigned installer and record that signing was skipped.

#### Scenario: Signing secrets present
- **WHEN** Authenticode secrets are configured
- **THEN** the published installer and executable are signed

#### Scenario: Signing secrets absent
- **WHEN** Authenticode secrets are not configured
- **THEN** CI still publishes an unsigned installer for internal use

