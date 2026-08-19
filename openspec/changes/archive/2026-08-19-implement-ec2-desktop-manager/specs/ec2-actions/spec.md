## Purpose

Lets operators start, stop, and restart permitted instances with confirmation, polling, and clear handling of AWS permission and state errors.

## ADDED Requirements

### Requirement: Start instance
The application SHALL start the selected instance only when its ID came from the current inventory, then call StartInstances and poll until the instance is running or the wait times out.

#### Scenario: Successful start
- **WHEN** the user starts a stopped instance that IAM allows
- **THEN** the application calls StartInstances, shows a pending/starting state, and updates to running when AWS reports that state

### Requirement: Stop instance with confirmation
The application SHALL stop the selected running instance only after confirmation, then call StopInstances and poll until stopped or the wait times out. The confirmation MUST warn that active users can be disconnected.

#### Scenario: Successful stop
- **WHEN** the user confirms Stop on a running instance that IAM allows
- **THEN** the application calls StopInstances, shows stopping, and enables Start when AWS reports stopped

#### Scenario: Stop cancelled
- **WHEN** the user cancels the Stop confirmation
- **THEN** no StopInstances call is made

### Requirement: Restart instance with confirmation
The application SHALL reboot the selected running instance only after confirmation, then call RebootInstances (not Stop/Start) and wait until the instance returns to running or the wait times out.

#### Scenario: Successful restart
- **WHEN** the user confirms Restart on a running instance that IAM allows
- **THEN** the application calls RebootInstances, shows rebooting, and returns to running when AWS reports that state

### Requirement: Polling policy
The application SHALL poll action status first after 5 seconds, refresh normally every 15 seconds, wait at most 10 minutes, and after timeout show a warning and allow manual refresh.

#### Scenario: Action timeout
- **WHEN** the instance has not reached the expected state within 10 minutes
- **THEN** the application shows a timeout warning and allows the user to refresh manually

### Requirement: No automatic retry of Stop or Restart
The application MUST NOT automatically retry Stop or Restart after an error or ambiguous result without a new user confirmation.

#### Scenario: Stop fails
- **WHEN** StopInstances fails
- **THEN** the application reports the error and does not send another StopInstances request unless the user confirms Stop again

### Requirement: IAM remains authoritative
The application SHALL treat AWS API responses as authoritative. UI enablement is convenience only. AccessDenied and UnauthorizedOperation MUST produce a short message that AWS policy does not allow the operation.

#### Scenario: Restart denied by IAM
- **WHEN** RebootInstances returns AccessDenied or UnauthorizedOperation
- **THEN** the user sees that AWS policy does not allow Restart for this instance

### Requirement: Invalid state and missing instance
The application SHALL map invalid-state and missing-instance AWS errors to short user messages without retrying the action.

#### Scenario: Instance not found
- **WHEN** the action target is no longer visible in the region
- **THEN** the user is told the instance no longer exists or is not visible in this region

#### Scenario: Invalid state
- **WHEN** AWS rejects the action because of instance state
- **THEN** the user is told the requested action is not valid for the current instance state

### Requirement: Network errors
When AWS cannot be reached, the application SHALL tell the user to check the network connection and MUST NOT retry Stop or Restart automatically.

#### Scenario: Timeout contacting AWS
- **WHEN** an action or refresh fails due to network timeout
- **THEN** the status panel shows that AWS could not be reached
