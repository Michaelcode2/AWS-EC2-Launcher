## Purpose

Provides the Windows desktop window operators use to select a profile, view instances, trigger allowed actions, and see status without entering AWS passwords into the application.

## ADDED Requirements

### Requirement: Main window contents
The application SHALL present a main window that includes a customer profile selector, authenticated AWS account ID and identity, region selector, refresh control, instance table, selected-instance details, Start, Stop, Restart, and optional Connect RDP controls, an activity/status panel, and a logout control.

#### Scenario: Main window after successful login
- **WHEN** authentication and account verification succeed
- **THEN** the main window is shown with profile, account identity, region, instance table, action controls, status panel, and logout

### Requirement: Instance table columns
The instance table SHALL display Name, Instance ID, State, Instance type, Availability Zone, Private IP, Public IP, Elastic IP, Environment tag, and last refresh time.

#### Scenario: Table populated from inventory
- **WHEN** inventory is loaded
- **THEN** each visible instance appears as a row with the required columns

### Requirement: Action button enablement by instance state
The application SHALL enable Start, Stop, and Restart only according to the current instance state: Start only when `stopped`; Stop and Restart only when `running`; all three disabled for `pending`, `stopping`, `rebooting`, `shutting-down`, and `terminated`.

#### Scenario: Stopped instance selected
- **WHEN** the selected instance state is `stopped`
- **THEN** Start is enabled and Stop and Restart are disabled

#### Scenario: Running instance selected
- **WHEN** the selected instance state is `running`
- **THEN** Stop and Restart are enabled and Start is disabled

#### Scenario: Transitional instance selected
- **WHEN** the selected instance state is `pending`, `stopping`, `rebooting`, `shutting-down`, or `terminated`
- **THEN** Start, Stop, and Restart are disabled

### Requirement: Buttons disabled during in-flight actions
The application SHALL disable Start, Stop, and Restart for the selected instance while an action is in progress and the instance is transitioning.

#### Scenario: Start in progress
- **WHEN** the user starts a stopped instance and the instance has not yet reached a terminal polled state
- **THEN** the action buttons for that instance remain disabled until polling completes or times out

### Requirement: Confirmation for disruptive actions
The application SHALL require confirmation before Stop and Restart. Start MUST NOT require confirmation by default, but MAY require confirmation when the user preference is enabled.

#### Scenario: Stop confirmation
- **WHEN** the user chooses Stop
- **THEN** a confirmation dialog is shown and the stop request is not sent until the user confirms

#### Scenario: Restart confirmation
- **WHEN** the user chooses Restart
- **THEN** a confirmation dialog is shown and the reboot request is not sent until the user confirms

#### Scenario: Default start without confirmation
- **WHEN** the user chooses Start and the confirm-start preference is disabled
- **THEN** the start request is sent without a confirmation dialog

### Requirement: No AWS password prompt in the application
The application MUST NEVER present a field that asks the user to type an AWS console password into the application.

#### Scenario: Login uses external identity flow
- **WHEN** the user signs in
- **THEN** authentication occurs through the configured external AWS login flow rather than an in-app AWS password field

### Requirement: Feature flags hide actions
When a profile feature flag for Start, Stop, or Restart is false, the application SHALL hide that action. A true flag MUST NOT grant an action that AWS IAM denies.

#### Scenario: Restart hidden by profile
- **WHEN** the selected profile has restart disabled
- **THEN** the Restart control is not shown
