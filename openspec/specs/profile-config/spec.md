# profile-config Specification

## Purpose
Loads human-readable TOML customer profiles that control presentation, filters, and feature visibility without storing secrets or acting as authorization.
## Requirements
### Requirement: TOML profile structure
The application SHALL load profiles from TOML that include application name, expected account ID, default region, refresh interval, AWS profile name, filter mode, optional RDP settings, and feature flags for Start, Stop, and Restart.

#### Scenario: Valid example profile loads
- **WHEN** a valid example profile is selected
- **THEN** the application uses its account ID, region, AWS profile, filters, and feature flags

### Requirement: Validation of required fields
The application SHALL reject a profile that is missing expected account ID, default region, or AWS profile name, and SHALL require a region before operating.

#### Scenario: Missing region
- **WHEN** the user attempts to operate without a configured or selected region
- **THEN** the application tells the user to select or configure an AWS region

#### Scenario: Invalid TOML
- **WHEN** the profile file cannot be parsed or fails validation
- **THEN** the application shows a configuration error and does not open the main window

### Requirement: Secrets forbidden in configuration
Configuration files MUST NOT store AWS secret access keys, AWS console passwords, Windows passwords, plaintext refresh tokens, or private keys.

#### Scenario: Example profile is secret-free
- **WHEN** the shipped example profile is inspected
- **THEN** it contains no secret keys, passwords, or tokens

### Requirement: Multiple profiles
The application SHALL support multiple customer/account profiles from the first release, even if the initial operational use is one account and one region.

#### Scenario: Profile selector lists configured profiles
- **WHEN** more than one valid profile is present
- **THEN** the user can select among them before login

### Requirement: Feature flags are presentation only
A feature flag set to true MUST NOT be treated as permission. A feature flag set to false SHALL hide the corresponding action in the UI.

#### Scenario: Stop hidden
- **WHEN** `allow_stop` is false
- **THEN** Stop is not shown even if the instance is running

