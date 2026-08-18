# EC2 Desktop Manager
## Final Architecture and Development Specification

**Document status:** Development baseline  
**Version:** 1.0  
**Target platform:** Windows 10/11 x64  
**Primary implementation:** Python + PySide6 + Boto3 + Nuitka  
**Primary use case:** Authenticated desktop users manage permitted Amazon EC2 instances without a per-account web application.

---

## 1. Executive decision

Build a Windows desktop application that authenticates the user through AWS IAM Identity Center, discovers EC2 instances in the configured account and region, applies optional local filters, and exposes Start, Stop, and Restart actions. AWS IAM remains the authoritative security boundary; the application configuration only controls presentation and convenience.

The first release should not require S3, CloudFront, API Gateway, Lambda, or a web authorization page in every customer account. The desktop application communicates directly with AWS APIs using temporary credentials. IAM Identity Center and federated access are preferred over long-term IAM access keys for programmatic access [web:120][web:124].

Automatic shutdown after one hour without active Windows sessions is implemented independently on the EC2 instance as a Windows Scheduled Task. This ensures auto-stop continues when the desktop client is closed.

---

## 2. Goals and non-goals

### Goals

- Provide a simple Windows GUI for daily EC2 management.
- Authenticate without collecting AWS console passwords.
- Use temporary AWS credentials where possible.
- List instances visible to the authenticated AWS principal.
- Filter visible instances using application configuration.
- Enable Start, Stop, and Restart only when the state allows the operation.
- Let IAM enforce the final permission decision.
- Support multiple AWS accounts, regions, and customer configurations.
- Display instance state, name, ID, type, IP addresses, and Elastic IP.
- Open an RDP session to a configured Windows instance.
- Keep the Elastic IP stable across EC2 stop/start operations.
- Support automatic stop after 60 minutes without active sessions.
- Produce a distributable signed Windows installer.

### Non-goals for version 1

- Creating new EC2 instances.
- Modifying security groups, IAM policies, networks, or disks.
- Retrieving or displaying Windows administrator passwords.
- Managing arbitrary AWS resources.
- Replacing the AWS Management Console.
- Implementing a custom identity provider.
- Embedding long-term AWS access keys in the executable.
- Providing centralized fleet monitoring across all customers.

---

## 3. High-level architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ Customer Windows workstation                                 │
│                                                              │
│  EC2 Desktop Manager                                         │
│  ├─ PySide6 GUI                                              │
│  ├─ Authentication/session service                           │
│  ├─ EC2 discovery and filtering                              │
│  ├─ Action controller                                        │
│  ├─ Status polling                                           │
│  ├─ RDP launcher                                             │
│  └─ Local configuration                                      │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTPS / AWS SDK
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Customer AWS account                                         │
│                                                              │
│ IAM Identity Center / federated identity                     │
│ IAM permission set or federated role                         │
│        │                                                     │
│        ▼                                                     │
│ EC2 API: Describe / Start / Stop / Reboot                    │
│                                                              │
│ EC2 instance                                                 │
│ ├─ Elastic IP                                                │
│ ├─ Instance profile                                          │
│ └─ Windows Scheduled Task for idle auto-stop                 │
└──────────────────────────────────────────────────────────────┘
```

The desktop application is a client, not a trusted backend. Assume a user can inspect or modify the application. No authorization decision must depend on hidden values in the executable or a local configuration file.

---

## 4. User experience

### Login flow

1. User starts the application.
2. User selects a customer/account profile.
3. Application launches the AWS browser authentication flow or invokes the configured AWS SSO login process.
4. User authenticates through IAM Identity Center.
5. The application creates a Boto3 session using the SSO profile.
6. The application calls STS `GetCallerIdentity`.
7. The returned AWS account ID is compared with the profile's expected account ID.
8. The main window opens only after the account check succeeds.

The application must never ask the user to type an AWS console password into the application.

### Main window

The main window contains:

- Customer profile selector.
- AWS account ID and authenticated identity.
- Region selector.
- Refresh button.
- Instance table.
- Selected-instance details.
- Start, Stop, Restart, and optional Connect RDP buttons.
- Activity/status panel.
- Logout button.

Suggested table columns:

- Name.
- Instance ID.
- State.
- Instance type.
- Availability Zone.
- Private IP.
- Public IP.
- Elastic IP.
- Environment tag.
- Last refresh time.

### Button behavior

| EC2 state | Start | Stop | Restart |
|---|---:|---:|---:|
| `stopped` | Enabled | Disabled | Disabled |
| `pending` | Disabled | Disabled | Disabled |
| `running` | Disabled | Enabled | Enabled |
| `stopping` | Disabled | Disabled | Disabled |
| `rebooting` | Disabled | Disabled | Disabled |
| `shutting-down` | Disabled | Disabled | Disabled |
| `terminated` | Disabled | Disabled | Disabled |

The UI state is only a convenience. The API response remains authoritative. An operation can still fail with `AccessDenied` when the IAM policy does not allow that action.

Stop and Restart require confirmation. Start can require confirmation through a user preference, but the default should be one click followed by progress feedback.

---

## 5. Authentication and authorization

### Preferred authentication

Use AWS IAM Identity Center with an AWS SDK SSO profile. AWS SDKs support IAM Identity Center credentials, and the resulting credentials are temporary and refreshable through the SDK/CLI credential mechanism [web:85][web:61][web:122].

The initial implementation may use AWS CLI v2 for the browser login:

```powershell
aws sso login --profile customer-server
```

Boto3 then uses the configured profile:

```python
import boto3

session = boto3.Session(
    profile_name="customer-server",
    region_name="eu-central-1",
)
```

The future implementation may use direct SSO device authorization, but that is not required for the first release.

### Fallback authentication

If a customer cannot use IAM Identity Center, support a separate fallback profile based on a customer-created IAM user with programmatic access. This mode is lower priority and must include:

- Least-privilege policy.
- Windows Credential Manager or DPAPI-protected storage.
- No plaintext secrets in configuration files.
- Key rotation instructions.
- Credential revocation instructions.
- Clear warning that long-term keys are less desirable than temporary credentials.

### Required IAM permissions

The minimum read/action policy is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadEc2Inventory",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeTags",
        "ec2:DescribeInstanceStatus"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ManageApprovedInstances",
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:RebootInstances"
      ],
      "Resource": [
        "arn:aws:ec2:eu-central-1:123456789012:instance/i-0123456789abcdef0"
      ]
    }
  ]
}
```

AWS identity-based policies define which EC2 actions a user, group, permission set, or role can perform and on which resources [web:119]. `Describe*` actions commonly require a wildcard resource while Start, Stop, and Reboot can be restricted to approved instance ARNs.

Remove `ec2:RebootInstances` if Restart must not be available. Remove `ec2:StopInstances` if users may start but not stop instances.

### Authorization principle

The application must not attempt to become the authorization system. It should:

- Render known-valid actions based on instance state.
- Attempt the selected AWS API action.
- Handle `AccessDenied` and `UnauthorizedOperation` clearly.
- Never ask for broader permissions merely to predict whether a button will succeed.

Example error:

```text
AWS policy does not allow Restart for this instance.
Contact the AWS administrator if this operation is required.
```

---

## 6. EC2 discovery and filtering

### Discovery

The application calls `DescribeInstances` through a paginator. It should support multiple reservations and multiple pages. The inventory service converts AWS responses into internal `Ec2Instance` objects.

Each instance should include:

```python
@dataclass
class Ec2Instance:
    instance_id: str
    name: str
    state: str
    instance_type: str
    availability_zone: str | None
    private_ip: str | None
    public_ip: str | None
    elastic_ip: str | None
    tags: dict[str, str]
```

The AWS Boto3 EC2 examples use `describe_instances` for instance inventory and provide SDK operations for EC2 management [web:100].

### Supported filters

#### All visible instances

```toml
[filters]
mode = "all"
```

#### Explicit instance IDs

```toml
[filters]
mode = "instance_ids"
instance_ids = [
  "i-0123456789abcdef0",
  "i-0456789abcdef0123"
]
```

#### Tags

```toml
[filters]
mode = "tags"

[filters.tags]
ManagedBy = "ec2-desktop-manager"
Customer = "example-customer"
```

Tags are the recommended filter for maintainability because a replacement instance can retain the same management tags even when its instance ID changes.

### Filter security rule

The configuration filter can only reduce what the user sees. It must never grant access to an instance that IAM does not authorize. If a user changes the configuration to include another instance, the AWS policy still decides whether actions succeed.

---

## 7. EC2 action workflow

### Start

1. User selects a stopped instance.
2. Application validates the instance ID came from the current inventory.
3. Application calls `StartInstances`.
4. UI changes to `pending` / `starting`.
5. Action buttons are disabled during the transition.
6. Application polls `DescribeInstances` and optionally `DescribeInstanceStatus`.
7. UI changes to `running` when the state is confirmed.
8. For Windows, optionally test RDP availability before enabling Connect.

### Stop

1. User selects a running instance.
2. Application displays a confirmation dialog.
3. Application calls `StopInstances`.
4. UI changes to `stopping`.
5. Application polls until `stopped`.
6. UI enables Start.

The customer must understand that stopping a Windows server can disconnect active users and may interrupt unsaved work.

### Restart

1. User selects a running instance.
2. Application displays a confirmation dialog.
3. Application calls `RebootInstances`.
4. UI changes to `rebooting`.
5. Application waits for the instance to return to `running`.
6. Optional RDP readiness check is performed.

Restart is an EC2 reboot operation, not a Stop/Start cycle. It should have its own IAM action and its own user-facing warning.

### Polling policy

- Initial action status poll: 5 seconds.
- Normal refresh interval: 15 seconds.
- Maximum action wait: 10 minutes.
- After timeout: show a warning and allow manual refresh.
- Never perform an automatic retry of Stop or Restart without user approval.

---

## 8. Elastic IP and RDP

Each managed Windows instance may have an Elastic IP configured in the profile or discovered through EC2 network data. The application should display the Elastic IP and use it for RDP.

The user flow is:

```text
Start instance → Wait for running → Wait for Windows/RDP → Connect RDP
```

The application may launch:

```powershell
mstsc.exe /v:203.0.113.25
```

Do not store the Windows password in the application. The user authenticates to Windows through the normal RDP credential process.

RDP security remains an AWS/network responsibility:

- Do not expose TCP 3389 to `0.0.0.0/0`.
- Restrict RDP to approved public IP ranges, VPN, or a private network.
- Prefer Systems Manager or a VPN-based access path where practical.
- The Elastic IP is an address, not an authentication mechanism.

---

## 9. Automatic stop after one hour

The desktop application must not own the idle timer because it may be closed or disconnected. Install an independent Windows Scheduled Task on the EC2 instance.

### Recommended implementation

```text
Windows Scheduled Task
        │ every 5–10 minutes
        ▼
PowerShell idle-check script
        │
        ├─ Query active sessions with query user/quser
        ├─ Detect Active RDP or console sessions
        ├─ Update last-active timestamp
        └─ Stop the instance after 60 minutes of no activity
```

The script should use the EC2 instance profile for temporary AWS credentials. It must not contain an IAM access key or secret.

The instance role requires only:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StopThisInstanceOnly",
      "Effect": "Allow",
      "Action": "ec2:StopInstances",
      "Resource": "arn:aws:ec2:eu-central-1:123456789012:instance/i-0123456789abcdef0"
    }
  ]
}
```

### Idle algorithm

1. If the Windows session check finds an active session, save `last_active = now`.
2. If no active session exists and no timestamp exists, save `last_active = now`.
3. If no active session exists and elapsed time is less than 60 minutes, do nothing.
4. If no active session exists and elapsed time is at least 60 minutes, call `StopInstances` for the local instance.
5. Write an operational log locally and to Windows Event Log.
6. Do not stop if the script cannot reliably determine session status.

A safe failure mode is to leave the server running rather than stop it unexpectedly.

### Optional SSM alternative

AWS Systems Manager Run Command can remotely and securely manage configured EC2 managed nodes through the AWS SDK, CLI, or PowerShell [web:29]. It can be used instead of the local task if a customer wants centralized automation, but it requires additional per-account SSM, EventBridge, and Lambda components.

---

## 10. Application configuration

Use TOML for human-readable profiles.

```toml
[application]
name = "Example Customer"
expected_account_id = "123456789012"
default_region = "eu-central-1"
refresh_interval_seconds = 15

[aws]
profile = "customer-server"

[filters]
mode = "tags"

[filters.tags]
ManagedBy = "ec2-desktop-manager"
Customer = "example-customer"

[rdp]
enabled = true
use_elastic_ip = true

[features]
allow_start = true
allow_stop = true
allow_restart = true
```

The `features` values control what the customer sees, but IAM remains authoritative. A false value hides an action; a true value does not grant an action.

Never store:

- AWS secret access keys.
- AWS console passwords.
- Windows passwords.
- Refresh tokens in plaintext.
- Private keys.

---

## 11. Software architecture

### Project structure

```text
ec2-desktop-manager/
├── pyproject.toml
├── README.md
├── LICENSE
├── assets/
│   └── app.ico
├── config/
│   └── example-profile.toml
├── src/
│   └── ec2_manager/
│       ├── __init__.py
│       ├── main.py
│       ├── version.py
│       ├── gui/
│       │   ├── main_window.py
│       │   ├── instance_table.py
│       │   ├── dialogs.py
│       │   └── workers.py
│       ├── aws/
│       │   ├── session.py
│       │   ├── identity.py
│       │   ├── inventory.py
│       │   ├── actions.py
│       │   └── errors.py
│       ├── config/
│       │   ├── loader.py
│       │   ├── models.py
│       │   └── validation.py
│       ├── rdp/
│       │   └── launcher.py
│       └── logging_config.py
├── tests/
│   ├── test_filters.py
│   ├── test_state_logic.py
│   ├── test_config.py
│   └── test_aws_actions.py
└── installer/
    └── ec2-manager.iss
```

### Layers

#### GUI layer

Responsible for windows, tables, buttons, dialogs, and visual state. It must not contain raw AWS policy or credential logic.

#### Application layer

Responsible for use cases:

- Authenticate.
- Verify account.
- Refresh inventory.
- Filter inventory.
- Start instance.
- Stop instance.
- Restart instance.
- Wait for state transition.
- Launch RDP.

#### AWS adapter layer

Responsible for Boto3 sessions, EC2 API calls, STS identity, error mapping, paginators, and waiters/polling.

#### Configuration layer

Responsible for TOML loading, validation, profile selection, and default values.

#### Platform layer

Responsible for launching `mstsc.exe`, opening the AWS login flow, Windows credential integration if later required, and installer integration.

---

## 12. Technology decisions

### Python

Selected because the developer already knows Python and Boto3 provides direct access to EC2 and IAM Identity Center profiles.

### PySide6

Selected for a complete desktop GUI toolkit with tables, dialogs, workers, signals, and good Windows support. Avoid Tkinter for the production application unless the UI remains extremely small.

### Boto3

Selected as the official AWS SDK for Python. It provides EC2 APIs, STS, profile-based credentials, and IAM Identity Center support [web:85][web:100].

### Nuitka

Use Nuitka to produce standalone or one-file Windows builds. Begin with standalone mode during development because packaging problems are easier to debug, then evaluate one-file mode for distribution [web:90][web:92].

### Installer

Use Inno Setup for the first release. The installer should:

- Install the application under Program Files.
- Install the application icon and shortcuts.
- Create a per-user configuration directory.
- Offer optional AWS CLI prerequisite detection.
- Register the product in Windows Apps.
- Support uninstall.
- Never write credentials into the installation directory.

### Code signing

Before customer distribution, sign the installer and executable with an Authenticode certificate. Unsigned administrative applications are more likely to trigger Windows SmartScreen or antivirus warnings.

---

## 13. Error handling

Map technical AWS errors into user-friendly messages.

| Technical condition | User message |
|---|---|
| `AccessDenied` | Your AWS policy does not allow this operation. |
| `UnauthorizedOperation` | Your AWS policy does not allow this operation. |
| Expired SSO token | AWS login has expired. Please sign in again. |
| Wrong account | The selected profile authenticated to a different AWS account. |
| Instance not found | The instance no longer exists or is not visible in this region. |
| Invalid state | The requested action is not valid for the current instance state. |
| Network timeout | AWS could not be reached. Check your network connection. |
| RDP unavailable | EC2 is running, but Windows/RDP is not ready yet. |
| Missing region | Select or configure an AWS region. |

Log the detailed exception locally, but show the user a short, actionable message.

Never log:

- Secret access keys.
- Session tokens.
- Passwords.
- Full credential files.
- Sensitive RDP credentials.

---

## 14. Logging and audit

### Local application log

Store logs in a per-user application data directory, for example:

```text
%LOCALAPPDATA%\Ec2DesktopManager\logs\app.log
```

Record:

- Application version.
- Profile name, not secret values.
- AWS account ID.
- Region.
- Instance ID.
- Requested action.
- Result.
- Error code.
- Timestamp.
- Authenticated principal when available.

### AWS audit

EC2 API calls should be visible in AWS CloudTrail. The customer can use CloudTrail to determine which identity started, stopped, or rebooted an instance.

The application should not attempt to create its own audit system in version 1.

---

## 15. Security requirements

- Use IAM Identity Center or federation with temporary credentials as the default.
- Never embed credentials in the executable.
- Never treat a local configuration file as authorization.
- Validate the authenticated account ID with STS.
- Restrict IAM actions to the required EC2 operations.
- Restrict Start, Stop, and Reboot to approved instance ARNs where possible.
- Use an instance profile for the local auto-stop task.
- Do not expose RDP to the entire internet.
- Keep the configured instance ID and account ID separate from secrets.
- Do not automatically retry Stop or Restart after an ambiguous error.
- Confirm disruptive actions.
- Sign the production executable and installer.
- Protect configuration and logs with normal Windows ACLs.
- Keep dependencies updated and scan release artifacts.
- Treat the desktop application as an untrusted client.

AWS recommends temporary credentials for workforce identities and programmatic SDK/CLI access rather than long-term IAM access keys [web:120][web:124].

---

## 16. Development phases

### Phase 1: project foundation

- Create Python project with `pyproject.toml`.
- Add PySide6, Boto3, pytest, mypy/ruff if desired.
- Define configuration models.
- Create the main window shell.
- Add application logging.

### Phase 2: authentication

- Detect AWS CLI installation.
- Load the selected SSO profile.
- Run or guide the user through SSO login.
- Create a Boto3 session.
- Validate account identity with STS.
- Display authenticated account and principal.

### Phase 3: inventory

- Implement regional EC2 discovery.
- Add pagination.
- Convert AWS responses into internal models.
- Add state and tag filtering.
- Populate the instance table.
- Add manual and timed refresh.

### Phase 4: actions

- Implement Start.
- Implement Stop with confirmation.
- Implement Restart with confirmation.
- Add state-transition polling.
- Map AccessDenied and common AWS errors.
- Add unit tests with mocked Boto3 clients.

### Phase 5: RDP

- Display Elastic IP.
- Add RDP readiness status.
- Launch `mstsc.exe`.
- Add a configurable RDP button.

### Phase 6: auto-stop package

- Create the PowerShell session-check script.
- Create the Windows Scheduled Task installer.
- Create the instance-profile policy.
- Test active, disconnected, and no-session states.
- Test safe behavior when AWS is unavailable.

### Phase 7: packaging

- Build Nuitka standalone output.
- Add application icon.
- Create Inno Setup installer.
- Add version metadata.
- Sign executable and installer.
- Test on a clean Windows VM.

### Phase 8: pilot release

- Test with one internal AWS account.
- Test with one external/customer-style account.
- Verify IAM restrictions.
- Verify wrong-account protection.
- Verify action denial messages.
- Verify auto-stop after a shortened test interval.
- Document customer onboarding.

---

## 17. Acceptance criteria

### Authentication

- User can authenticate without entering an AWS console password into the application.
- Application displays the AWS account ID after login.
- Application refuses to operate when the account ID does not match the profile.
- Expired credentials produce a clear re-login message.

### Inventory

- Application lists all visible instances in the configured region.
- Pagination works with more than one API page.
- Instance names are taken from the `Name` tag, with instance ID fallback.
- Tag and instance-ID filters work.
- Refresh updates state correctly.

### Actions

- Start works when IAM permits it.
- Stop works when IAM permits it.
- Restart works when IAM permits it.
- Unauthorized actions show a clear message.
- Buttons are disabled during invalid states and transitions.
- Stop and Restart require confirmation.
- The application does not retry destructive actions automatically.

### RDP

- Elastic IP is displayed correctly.
- Connect RDP launches the Windows RDP client.
- RDP is not enabled until the instance is running and optionally reachable.

### Auto-stop

- Active sessions prevent shutdown.
- No active session for 60 minutes triggers shutdown.
- AWS/API failure fails safe and leaves the instance running.
- The task works when the desktop client is closed.

### Distribution

- Installer works on a clean supported Windows machine.
- Python is not required on the customer computer.
- Executable and installer are signed.
- No secrets are included in the build artifacts.

---

## 18. Initial implementation recommendation

Start with one AWS account profile and one region, but design the data models for multiple profiles from the beginning.

The recommended MVP is:

```text
PySide6 GUI
Boto3 EC2 and STS integration
AWS CLI-based IAM Identity Center login
TOML customer configuration
Instance listing with tag filtering
Start / Stop / Restart
State polling
Elastic IP display
RDP launcher
PowerShell auto-stop task
Nuitka standalone build
Inno Setup installer
```

Do not begin with direct custom SSO implementation, multi-region discovery, EC2 provisioning, or a web backend. Those can be added after the single-account workflow is stable.

The most important architectural rule is: **the application improves usability, but AWS IAM decides what the user is allowed to do**. This preserves a secure permission boundary while giving customers a convenient desktop control panel.
