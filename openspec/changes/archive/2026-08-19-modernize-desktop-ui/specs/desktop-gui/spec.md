## ADDED Requirements

### Requirement: Consistent visual theme
The application SHALL apply one visual theme to the login window, main window, instance table, confirmation dialogs, and configuration-error dialogs. The theme MUST use consistent spacing, typography, and control styling so windows do not look like unstyled system dialogs mixed with a custom main window.

#### Scenario: Login and main window share the theme
- **WHEN** the operator opens the login window and later the main window
- **THEN** both windows use the same colors, type scale, and control styling

#### Scenario: Confirmation dialogs match the theme
- **WHEN** the operator is asked to confirm Stop or Restart
- **THEN** the confirmation dialog uses the same visual theme as the main window

### Requirement: Header identity hierarchy
The main window SHALL show the customer profile name, AWS account ID, and a shortened identity (not the full ARN as the primary header text). The full identity ARN MUST remain available without leaving the window (for example via tooltip or an expandable/copyable detail). Refresh and Logout MUST remain visible in the header.

#### Scenario: Header after successful login
- **WHEN** the main window is shown after authentication
- **THEN** the header displays the profile name, account ID, and a shortened identity, and does not use the full ARN as the primary identity label

#### Scenario: Full ARN still available
- **WHEN** the operator inspects identity details in the header
- **THEN** the full IAM ARN is visible without opening another application

### Requirement: Color-coded instance state
The instance table and the selected-instance summary SHALL present instance state with a color-coded status that distinguishes at least running, stopped, transitional (`pending`, `stopping`, `rebooting`, `shutting-down`), and terminated. State text MUST remain readable (the color is in addition to the state name, not a replacement for it).

#### Scenario: Stopped instance in the table
- **WHEN** inventory includes an instance whose state is `stopped`
- **THEN** that row's state is shown as `stopped` with a stopped-status color distinct from running

#### Scenario: Running instance in the table
- **WHEN** inventory includes an instance whose state is `running`
- **THEN** that row's state is shown as `running` with a running-status color distinct from stopped

#### Scenario: Selected-instance summary matches table state
- **WHEN** the operator selects an instance
- **THEN** the summary below the table shows the same state name and status coloring family as the table row

### Requirement: Action control affordances
Start, Stop, Restart, Connect RDP, Refresh, Logout, and Sign in SHALL include an icon and SHALL use visual weight that matches the action: Start and Sign in as primary, Stop as destructive, Restart and Connect RDP as secondary, Logout as a non-primary header action. Disabled actions MUST remain visually distinct from enabled ones. Feature flags and state-based enablement from existing requirements still apply.

#### Scenario: Stopped instance selected
- **WHEN** the selected instance state is `stopped` and Start is visible
- **THEN** Start is shown as an enabled primary action with an icon, and Stop and Restart appear disabled

#### Scenario: Sign in is the primary login action
- **WHEN** the login window is shown
- **THEN** Sign in is the visually primary control and includes an icon

### Requirement: Selected-instance panel
The area below the instance table SHALL present the selected instance as a distinct summary panel (not a single undifferentiated line of wrapping text). It MUST show name, instance ID, state, type, and network addresses the operator already sees today. When no instance is selected, it MUST show a clear empty-state message.

#### Scenario: Instance selected
- **WHEN** the operator selects a row in the instance table
- **THEN** the summary panel shows that instance's name, ID, state, type, and addresses in a scannable layout

#### Scenario: No instance selected
- **WHEN** no table row is selected
- **THEN** the summary panel tells the operator to select an instance

### Requirement: Activity panel readability
The Activity panel SHALL remain visible on the main window, SHALL keep chronological status messages, and SHALL use theme styling (background, type, and padding) that distinguishes the log from the instance table. New messages MUST still appear without clearing previous messages in the same session.

#### Scenario: Status after sign-in
- **WHEN** the main window opens after a successful login
- **THEN** the Activity panel shows a signed-in status using the application theme

#### Scenario: Messages accumulate
- **WHEN** the operator refreshes inventory
- **THEN** the Activity panel appends a refresh message and retains earlier messages from the session
