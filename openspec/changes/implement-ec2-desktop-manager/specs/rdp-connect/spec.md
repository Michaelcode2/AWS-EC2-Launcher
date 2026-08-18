## Purpose

Shows the instance Elastic IP and launches the Windows Remote Desktop client without storing Windows passwords in the application.

## ADDED Requirements

### Requirement: Display Elastic IP
The application SHALL display the Elastic IP for a managed instance when it is configured on the profile or discovered from EC2 network data.

#### Scenario: Elastic IP present
- **WHEN** an instance has an associated Elastic IP
- **THEN** the instance table and details show that address

### Requirement: Connect RDP uses Elastic IP when configured
When RDP is enabled and `use_elastic_ip` is true, the application SHALL launch the Windows Remote Desktop client against the Elastic IP.

#### Scenario: Connect launches mstsc
- **WHEN** the user chooses Connect RDP for a running instance with a known Elastic IP
- **THEN** the Windows RDP client is started targeting that address

### Requirement: RDP enabled only when running
The application SHALL keep Connect RDP disabled until the instance is running. When an optional readiness check is enabled, Connect RDP SHALL remain disabled until that check succeeds.

#### Scenario: Instance still starting
- **WHEN** the instance state is not `running`
- **THEN** Connect RDP is disabled

#### Scenario: Running but RDP not ready
- **WHEN** the instance is running and the optional RDP readiness check fails
- **THEN** Connect RDP remains disabled and the user is told EC2 is running but Windows/RDP is not ready yet

### Requirement: No Windows password storage
The application MUST NOT store, retrieve, or display Windows administrator or user passwords. The user authenticates to Windows through the normal RDP credential prompt.

#### Scenario: Connect does not supply a password
- **WHEN** Connect RDP is launched
- **THEN** the application does not inject or persist a Windows password
