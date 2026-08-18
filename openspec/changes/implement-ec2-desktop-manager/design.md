## Context

The repository currently contains OpenSpec scaffolding and `docs/Architecture.md`. There is no application code. See `proposal.md` for motivation and the delta specs for behavior. This design implements that architecture as a Python desktop client with IAM as the only authorization boundary.

Constraints that shape the approach:

- Target runtime is Windows 10/11 x64; customers must not need Python.
- Nuitka + PySide6 + Inno Setup require a Windows toolchain. Linux Docker cannot produce a trustworthy native Windows GUI binary.
- Developers may work on Linux, so tests that do not need Qt/Windows APIs must run in Docker.
- The desktop client is untrusted; local config never grants AWS permissions.

## Goals / Non-Goals

**Goals:**

- Layer GUI, use cases, AWS adapters, config, and platform code so AWS calls never live in widgets.
- Use AWS CLI v2 `sso login` for Identity Center in v1; Boto3 consumes the named profile.
- Compile and package on GitHub Actions `windows-latest`; run unit tests and linters in local Docker and in a Linux CI job.
- Ship idle-auto-stop as a separate on-instance package, not as a timer inside the desktop app.

**Non-Goals:**

- Cross-compiling the Windows GUI from Linux Docker or Wine.
- Direct SSO device-authorization (no AWS CLI) in v1.
- IAM user access-key fallback in v1 (deferred).
- Centralized SSM/EventBridge auto-stop.
- Creating instances, changing security groups, or retrieving Windows passwords.
- Requiring Authenticode in every CI run (signing is optional when secrets exist).

## Decisions

### 1. Language and GUI: Python 3.12 + PySide6

**Decision:** Implement `ec2_manager` as a Python 3.12 package with PySide6.

**Rationale:** Matches the architecture baseline, Boto3 is the AWS SDK of record, and PySide6 provides tables, dialogs, and worker threads on Windows.

**Alternatives considered:**

- Tkinter — rejected; too limited for the main window.
- C# / WPF — rejected; leaves the documented Python/Boto3 path.
- Electron — rejected; larger attack surface and no Boto3-native story.

### 2. Project layout

Follow the architecture tree, with CI/packaging added:

```text
.
├── pyproject.toml
├── Dockerfile                 # Linux test/lint image
├── docker-compose.yml         # `test` service
├── .github/workflows/
│   ├── test.yml               # Linux: ruff, mypy, pytest
│   └── build-windows.yml      # Windows: Nuitka + Inno Setup
├── src/ec2_manager/           # application package
├── tests/
├── config/example-profile.toml
├── scripts/idle-stop/         # PowerShell task + policy example
└── installer/ec2-manager.iss
```

Layers:

| Layer | Responsibility |
|---|---|
| GUI | Windows, table, dialogs, visual state. No raw AWS/credential logic. |
| Application | Authenticate, verify account, refresh, filter, start/stop/restart, wait, launch RDP. |
| AWS adapter | Boto3 session, STS, paginated Describe, Start/Stop/Reboot, error mapping. |
| Config | TOML load, validation, defaults. |
| Platform | `aws sso login`, `mstsc.exe`, paths under `%LOCALAPPDATA%`. |

AWS work runs on `QThread` / worker objects so the UI thread never blocks.

### 3. Authentication: AWS CLI SSO profile

**Decision:** Detect AWS CLI v2, run `aws sso login --profile <name>`, then `boto3.Session(profile_name=..., region_name=...)`. Call STS `GetCallerIdentity` and refuse to open the main window on account mismatch.

**Rationale:** Architecture v1 explicitly prefers CLI-based Identity Center over custom device authorization.

**Alternatives considered:**

- Embedded SSO OIDC in-process — deferred; more code and security review for little v1 gain.
- Long-term IAM keys in config — forbidden.
- Credential Manager IAM-user fallback — deferred after SSO MVP.

### 4. Inventory and actions

**Decision:** Paginate `describe_instances`. Convert to an internal dataclass. Apply profile filters in application code after the API returns. Actions accept only instance IDs present in the current inventory snapshot. Poll DescribeInstances: first wait 5s, then 15s, cap 10 minutes. Never auto-retry Stop/Reboot.

**Rationale:** Filters are presentation-only. IAM remains authoritative; UI buttons are convenience.

### 5. RDP

**Decision:** Show Elastic IP from association data (fallback to profile config). Launch `mstsc.exe /v:<address>`. Optional TCP 3389 probe before enabling Connect. Never store Windows passwords.

### 6. Idle auto-stop as a sibling artifact

**Decision:** Ship PowerShell + Scheduled Task installer under `scripts/idle-stop/`. Document instance-profile policy. The desktop app does not install or drive this timer.

**Rationale:** The client may be closed; fail-safe is leave running if session status is unknown.

### 7. Packaging: Nuitka standalone + Inno Setup

**Decision:** Nuitka `--standalone` for v1 (easier to debug than one-file). Inno Setup installs to Program Files, shortcuts, per-user config dir, optional AWS CLI detection, uninstall. No credentials in the install directory.

**Alternatives considered:**

- PyInstaller — viable but architecture specifies Nuitka.
- One-file Nuitka in v1 — deferred until standalone is stable.
- MSI/WiX — more complex than Inno Setup for the first release.

### 8. Compile in GitHub Actions Windows; test in Docker

**Decision:**

| Path | What it does |
|---|---|
| `.github/workflows/test.yml` on `ubuntu-latest` | ruff, mypy, pytest (mocked AWS). Same commands as Docker. |
| `.github/workflows/build-windows.yml` on `windows-latest` | Install Python 3.12, AWS CLI is not bundled, Nuitka compile, Inno Setup, upload `.exe` installer artifact. Optional Authenticode if secrets exist. |
| `Dockerfile` + `docker-compose.yml` | Reproducible local `docker compose run --rm test` for lint/unit tests. |

**Rationale:** Qt/PySide6 Windows binaries and Inno Setup need a Windows runner. Linux Docker is the portable local verification path requested by the user. A single Linux container cannot replace the Windows compile.

**Alternatives considered:**

- Wine + Nuitka in Docker — rejected; Qt Windows builds via Wine are unreliable.
- Windows containers in Docker on Linux — not supported on a typical Linux host.
- Self-hosted Windows builder only — GitHub-hosted `windows-latest` is enough for v1; a local `scripts/build-windows.ps1` will mirror CI for developers who have Windows.

Signing: if `SIGNING_CERT_PFX` / password secrets are present, sign exe and installer; otherwise publish unsigned artifacts and log that signing was skipped.

### 9. Logging

**Decision:** Write `%LOCALAPPDATA%\Ec2DesktopManager\logs\app.log`. Log version, profile name, account ID, region, instance ID, action, result, error code, timestamp, principal. Never log secrets, session tokens, or credential files.

### 10. Testing strategy

- Unit tests with moto or botocore stubs for filters, state-button matrix, config validation, error mapping, idle-stop script parsing where practical.
- GUI smoke tests are manual on Windows (CI does not run the Qt window).
- Idle-stop session logic is unit-tested with injected `quser` fixtures; full Scheduled Task verification is a pilot checklist on a real instance.

## Risks / Trade-offs

- [Nuitka + PySide6 plugin surprises] → Start with standalone mode; pin versions; keep a Windows CI job that actually launches `--help` / a headless import check.
- [AWS CLI prerequisite] → Installer detects CLI and warns; document it as required for SSO login.
- [Unsigned SmartScreen warnings] → Optional signing path; document that production distribution needs a cert.
- [Linux developers cannot run the GUI locally] → Docker covers domain tests; GUI verification stays on Windows or CI artifacts.
- [SSO token expiry mid-session] → Map expired-token errors to re-login; do not retry Stop/Restart.
- [Idle-stop false shutdown] → Fail safe: unknown session status leaves the instance running.
- [User tampers with TOML filters] → Spec already treats filters as non-authorizing; IAM resource ARNs must be tight on the AWS side.

## Migration Plan

Greenfield. No existing users or data.

1. Land application, tests, Docker test path.
2. Enable Linux `test.yml` on every push.
3. Enable Windows `build-windows.yml` on tags and `main`.
4. Pilot with one internal account using unsigned CI artifacts.
5. Add signing secrets before external distribution.
6. Deploy idle-stop to the instance separately from the desktop installer.

Rollback: uninstall the Windows app; disable or delete the Scheduled Task on the instance; IAM permission sets are unchanged by the client.

## Open Questions

- Exact Nuitka plugin flags for PySide6 will be settled during the first Windows CI build; they do not change specs.
- Authenticode certificate source (internal vs purchased) is an ops choice and does not change packaging behavior.
