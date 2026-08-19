## Why

Operators need a simple Windows desktop client to start, stop, restart, and RDP into permitted EC2 instances without a per-account web app or long-term keys in the executable. The architecture in `docs/Architecture.md` is the development baseline; this change implements that application as a signed, distributable Windows product built in GitHub Actions (and testable locally via Docker).

## What Changes

- Add a PySide6 Windows desktop application that authenticates with AWS IAM Identity Center, lists filtered EC2 instances, and exposes Start, Stop, Restart, and Connect RDP.
- Add TOML customer profiles, STS account-ID verification, and user-facing AWS error mapping. IAM remains the authorization boundary.
- Add an independent PowerShell idle-auto-stop package for the Windows EC2 instance (Scheduled Task + instance-profile policy).
- Add Nuitka standalone packaging and an Inno Setup installer so customers do not need Python.
- Add GitHub Actions on `windows-latest` to compile, package, and publish unsigned (and optionally signed) installer artifacts.
- Add a local Docker workflow for lint, unit tests, and Linux-side verification of non-GUI logic.

## Capabilities

### New Capabilities

- `desktop-gui`: Main window, instance table, action buttons, confirmations, status panel, and profile/region selectors.
- `aws-authentication`: IAM Identity Center login via AWS CLI SSO profiles, Boto3 sessions, STS account check, logout, and expired-credential handling.
- `ec2-inventory`: Paginated `DescribeInstances`, internal instance models, tag/ID/all filters, and refresh.
- `ec2-actions`: Start, Stop, Restart with state-based UI enablement, confirmation, polling, and AccessDenied handling.
- `rdp-connect`: Elastic IP display and `mstsc.exe` launch after the instance is running.
- `profile-config`: TOML profile loading, validation, feature flags, and secret-free configuration.
- `instance-idle-stop`: On-instance Scheduled Task that stops the instance after 60 minutes with no active Windows sessions.
- `windows-distribution`: Nuitka build, Inno Setup installer, GitHub Actions Windows compile, local Docker test image, and optional Authenticode signing.

### Modified Capabilities

- None. This repository has no existing capability specs.

## Impact

- New Python package under `src/ec2_manager/` plus tests, example TOML, assets, Inno Setup script, Docker files, and `.github/workflows/`.
- Dependencies: Python 3.12, PySide6, Boto3, Nuitka, pytest, ruff/mypy, Inno Setup (CI Windows runner).
- No web backend, S3, Lambda, or API Gateway.
- Signing requires an Authenticode certificate as a GitHub Actions secret; unsigned CI artifacts remain valid for internal builds.
- Fallback IAM-user keys (Credential Manager) are deferred after the SSO MVP unless a customer cannot use Identity Center.
