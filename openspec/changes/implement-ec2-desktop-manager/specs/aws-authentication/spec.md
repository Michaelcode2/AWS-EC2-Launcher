## Purpose

Authenticates operators with temporary AWS credentials and verifies the signed-in account before any EC2 management window is shown.

## ADDED Requirements

### Requirement: IAM Identity Center login
The application SHALL authenticate using an AWS IAM Identity Center SSO profile and MUST NOT collect AWS console passwords inside the application.

#### Scenario: Successful SSO login
- **WHEN** the user selects a profile configured for IAM Identity Center and completes the external login
- **THEN** the application obtains a session for that profile using temporary credentials

### Requirement: Account ID verification before main window
The application SHALL call STS GetCallerIdentity after login, compare the returned account ID with the profile's expected account ID, and SHALL open the main window only when they match.

#### Scenario: Matching account
- **WHEN** GetCallerIdentity returns the expected account ID
- **THEN** the main window opens and displays the account ID and authenticated identity

#### Scenario: Mismatched account
- **WHEN** GetCallerIdentity returns an account ID that does not match the profile
- **THEN** the application refuses to operate and shows that the profile authenticated to a different AWS account

### Requirement: Expired credentials
When SSO credentials are expired or invalid, the application SHALL show that AWS login has expired and prompt the user to sign in again.

#### Scenario: Expired SSO token during use
- **WHEN** an AWS call fails because the SSO token is expired
- **THEN** the user sees a re-login message and can restart the login flow

### Requirement: Display authenticated identity
After successful verification, the application SHALL display the AWS account ID and the authenticated principal identity.

#### Scenario: Identity shown in main window
- **WHEN** login and account verification succeed
- **THEN** the main window shows the account ID and principal

### Requirement: Logout
The application SHALL provide logout that ends the current application session so a different profile can be selected.

#### Scenario: User logs out
- **WHEN** the user chooses Logout
- **THEN** the authenticated session is cleared from the application UI and the user can select a profile again

### Requirement: No embedded long-term keys
The application MUST NOT embed AWS access keys, secret keys, or session tokens in the executable or default configuration.

#### Scenario: Fresh install has no credentials
- **WHEN** a user inspects a newly installed application and its shipped configuration
- **THEN** no AWS secret access keys or session tokens are present
