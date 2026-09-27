## MODIFIED Requirements

### Requirement: Connect RDP uses Elastic IP when configured
When RDP is enabled and `use_elastic_ip` is true, the application SHALL launch the platform Remote Desktop client against the Elastic IP. On Windows the client is the Windows Remote Desktop client (`mstsc.exe`). On Linux the client is the first executable found on `PATH` among `xfreerdp`, `xfreerdp3`, and `wlfreerdp`, in that order. The launched command MUST NOT include a Windows password or a password argument.

#### Scenario: Connect launches mstsc
- **WHEN** the user on Windows chooses Connect RDP for a running instance with a known Elastic IP
- **THEN** `mstsc.exe` is started targeting that address and the command contains no password

#### Scenario: Connect launches FreeRDP on Linux
- **WHEN** the user on Linux chooses Connect RDP for a running instance with a known Elastic IP and at least one of `xfreerdp`, `xfreerdp3`, or `wlfreerdp` is on `PATH`
- **THEN** the first of those clients found in that order is started targeting that address and the command contains no password

#### Scenario: FreeRDP client missing
- **WHEN** the user on Linux chooses Connect RDP and none of `xfreerdp`, `xfreerdp3`, or `wlfreerdp` is on `PATH`
- **THEN** the application reports that a FreeRDP client must be installed and does not start another program
