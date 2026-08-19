## Purpose

Stops a Windows EC2 instance after sixty minutes with no active local or RDP sessions, independently of whether the desktop client is open.

## ADDED Requirements

### Requirement: Independent on-instance task
Idle auto-stop SHALL run as a Windows Scheduled Task on the EC2 instance. The desktop application MUST NOT be required for the idle timer to operate.

#### Scenario: Desktop client closed
- **WHEN** the desktop client is closed and the instance has had no active sessions for 60 minutes
- **THEN** the on-instance task still stops the instance if session checks succeed

### Requirement: Idle algorithm
The task SHALL query active Windows sessions. If an active session exists, it SHALL record last-active as now. If no session exists and no timestamp exists, it SHALL record last-active as now. If no session exists and elapsed time is under 60 minutes, it SHALL do nothing. If no session exists and elapsed time is at least 60 minutes, it SHALL stop only the local instance.

#### Scenario: Active session present
- **WHEN** an Active RDP or console session is found
- **THEN** last-active is updated and the instance is not stopped

#### Scenario: Idle for 60 minutes
- **WHEN** no active session has existed for at least 60 minutes and session status was determined reliably
- **THEN** the task stops the local instance

### Requirement: Fail safe
If the task cannot reliably determine session status or cannot call AWS, it MUST leave the instance running rather than stop it.

#### Scenario: Session query fails
- **WHEN** the session check cannot determine whether users are active
- **THEN** the instance is left running

#### Scenario: Stop API unavailable
- **WHEN** the task cannot reach AWS to stop the instance
- **THEN** the instance is left running and the failure is logged

### Requirement: Instance profile credentials only
The task MUST use the EC2 instance profile for AWS credentials and MUST NOT contain an IAM access key or secret.

#### Scenario: Script has no access keys
- **WHEN** the shipped idle-stop script and task definition are inspected
- **THEN** they contain no AWS access key or secret

### Requirement: Local operational logging
The task SHALL write an operational log locally and to the Windows Event Log for session checks and stop attempts.

#### Scenario: Stop attempt logged
- **WHEN** the task stops the instance or skips a stop due to activity or failure
- **THEN** the outcome is recorded in the local log and Windows Event Log
