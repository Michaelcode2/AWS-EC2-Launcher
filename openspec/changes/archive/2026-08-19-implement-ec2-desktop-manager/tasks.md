## 1. Project foundation

- [x] 1.1 Create `pyproject.toml` for Python 3.12 with package `ec2_manager`, dependencies PySide6 and boto3, and dev extras for pytest, ruff, mypy, and Nuitka
- [x] 1.2 Scaffold `src/ec2_manager/` layers (`gui`, `aws`, `config`, `rdp`), `main.py`, `version.py`, and `logging_config.py`
- [x] 1.3 Add `assets/app.ico`, `LICENSE`, and a README that states IAM is the authorization boundary and Python is not required on customer PCs
- [x] 1.4 Add ruff and mypy configuration aligned with the package layout

## 2. Profile configuration

- [x] 2.1 Define TOML models for application, aws, filters (`all` / `instance_ids` / `tags`), rdp, and features
- [x] 2.2 Implement loader and validation that require expected account ID, default region, and AWS profile name
- [x] 2.3 Add `config/example-profile.toml` with no secrets and tag-based filters
- [x] 2.4 Add unit tests for valid profiles, missing fields, invalid TOML, and secret-free example file

## 3. AWS session and authentication

- [x] 3.1 Implement AWS CLI v2 detection and `aws sso login --profile` launch without any in-app AWS password field
- [x] 3.2 Create a Boto3 session from the selected profile and region
- [x] 3.3 Call STS GetCallerIdentity, refuse the main window on account mismatch, and display account ID plus principal on success
- [x] 3.4 Map expired SSO tokens to a re-login message and implement logout that clears the in-app session
- [x] 3.5 Add unit tests for matching account, mismatched account, and expired-token mapping

## 4. Inventory

- [x] 4.1 Implement paginated DescribeInstances conversion into the internal instance model (name from Name tag with instance ID fallback, IPs, Elastic IP, tags)
- [x] 4.2 Apply `all`, `instance_ids`, and `tags` filters after the API response without treating filters as authorization
- [x] 4.3 Add manual refresh and timed refresh using the profile interval (default 15 seconds)
- [x] 4.4 Add unit tests for pagination, name fallback, and each filter mode

## 5. Instance actions

- [x] 5.1 Implement StartInstances only for instance IDs from the current inventory snapshot
- [x] 5.2 Implement StopInstances and RebootInstances with confirmation; Restart MUST use RebootInstances, not Stop/Start
- [x] 5.3 Implement polling (5s first wait, 15s thereafter, 10 minute cap) with timeout warning and manual refresh
- [x] 5.4 Map AccessDenied, UnauthorizedOperation, invalid state, missing instance, and network timeout to short user messages
- [x] 5.5 Ensure Stop and Restart are never retried automatically after failure
- [x] 5.6 Add unit tests with mocked AWS clients for success, AccessDenied, invalid state, and no-retry behavior

## 6. Desktop GUI

- [x] 6.1 Build the main window with profile selector, account identity, region selector, refresh, instance table, details, actions, status panel, and logout
- [x] 6.2 Implement table columns: Name, Instance ID, State, Instance type, AZ, Private IP, Public IP, Elastic IP, Environment tag, last refresh
- [x] 6.3 Enable Start/Stop/Restart from instance state only; disable all three during transitions and in-flight actions
- [x] 6.4 Add Stop and Restart confirmation dialogs; Start confirms only when the user preference is on
- [x] 6.5 Hide actions when the matching feature flag is false
- [x] 6.6 Run AWS work on Qt workers so the UI thread never blocks
- [x] 6.7 Add unit tests for the button enablement matrix and feature-flag hiding

## 7. RDP connect

- [x] 7.1 Display Elastic IP from EC2 association data with profile fallback
- [x] 7.2 Launch `mstsc.exe /v:<address>` without storing or injecting a Windows password
- [x] 7.3 Disable Connect RDP until the instance is running; optional TCP 3389 readiness check with "not ready yet" status
- [x] 7.4 Add unit tests for address selection and disabled-when-not-running behavior

## 8. Logging

- [x] 8.1 Write logs to `%LOCALAPPDATA%\Ec2DesktopManager\logs\app.log` (with a sensible fallback path on Linux for tests)
- [x] 8.2 Log version, profile name, account ID, region, instance ID, action, result, error code, timestamp, and principal
- [x] 8.3 Redact secrets, session tokens, passwords, and credential file contents from logs
- [x] 8.4 Add unit tests that assert sensitive values are not written

## 9. Instance idle auto-stop package

- [x] 9.1 Add PowerShell idle-check script that uses instance-profile credentials only and implements the 60-minute idle algorithm
- [x] 9.2 Add Scheduled Task installer and example instance-profile policy limited to StopInstances on the local instance
- [x] 9.3 Fail safe: leave the instance running when session status or AWS is unavailable; log to a local file and Windows Event Log
- [x] 9.4 Add tests or fixtures covering active session, idle timeout, unknown session status, and AWS failure
- [x] 9.5 Document that this package is installed on the EC2 instance independently of the desktop client

## 10. Local Docker test path

- [x] 10.1 Add `Dockerfile` with Python 3.12 that installs the project plus test extras
- [x] 10.2 Add `docker-compose.yml` with a `test` service that runs ruff, mypy, and pytest
- [x] 10.3 Document `docker compose run --rm test` in the README as the local Linux verification path

## 11. Windows packaging

- [x] 11.1 Add Nuitka standalone build script (`scripts/build-windows.ps1`) with version metadata and application icon
- [x] 11.2 Add Inno Setup script that installs to Program Files, creates shortcuts, creates a per-user config directory, optionally detects AWS CLI, registers Apps & Features, supports uninstall, and writes no credentials
- [x] 11.3 Document that production distribution should be Authenticode-signed and that unsigned builds are for internal use

## 12. GitHub Actions

- [x] 12.1 Add `.github/workflows/test.yml` on `ubuntu-latest` running the same ruff, mypy, and pytest commands as Docker
- [x] 12.2 Add `.github/workflows/build-windows.yml` on `windows-latest` that compiles with Nuitka, builds the Inno Setup installer, and uploads the installer artifact
- [x] 12.3 Gate Authenticode signing on the presence of certificate secrets; skip signing and still publish the unsigned installer when secrets are absent
- [x] 12.4 Verify CI artifacts contain no AWS keys, passwords, or private keys

## 13. Documentation

- [x] 13.1 Document customer onboarding: IAM Identity Center profile, least-privilege policy, TOML profile, AWS CLI requirement
- [x] 13.2 Document how to run tests in Docker and how to obtain the Windows installer from GitHub Actions
- [x] 13.3 Add an IAM example policy matching Describe plus Start/Stop/Reboot on approved instance ARNs
