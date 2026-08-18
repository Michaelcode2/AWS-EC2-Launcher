# EC2 Desktop Manager

Windows desktop client for listing, starting, stopping, restarting, and
opening RDP to Amazon EC2 instances the signed-in principal is allowed to
manage.

**IAM remains the authorization boundary.** This application improves
usability. A local configuration file cannot grant access that AWS denies.
Customers do **not** need Python on their PCs; GitHub Actions produces a
standalone installer.

## Features

- IAM Identity Center sign-in through AWS CLI v2 (`aws sso login`)
- Account ID check with STS before the main window opens
- Paginated instance inventory with tag or instance-ID filters
- Start / Stop / Restart with confirmation and polling
- Elastic IP display and `mstsc.exe` launch
- Optional on-instance idle auto-stop (separate package)

## Develop on Linux, compile on Windows

Unit tests and linters run on Linux (locally or in Docker). The GUI can also
be started on Linux for layout work. RDP, the installer, and the shipped
`.exe` require Windows.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
ruff check src tests
mypy
pytest -q
```

Local Docker (same commands as CI):

```bash
docker compose run --rm test
```

## Windows installer

GitHub Actions workflow `build-windows` runs on `windows-latest`, compiles
with Nuitka, builds an Inno Setup installer, and uploads it as an artifact.
Download it from the workflow run. Unsigned artifacts are for internal use.
Production distribution should be Authenticode-signed by configuring
`SIGNING_CERT_PFX` and `SIGNING_CERT_PASSWORD` as repository secrets.

On a Windows machine you can also run:

```powershell
.\scripts\build-windows.ps1
```

## Configuration

See `docs/onboarding.md` and `config/example-profile.toml`. Profiles live in
`%LOCALAPPDATA%\Ec2DesktopManager\config\` after install.

## Idle auto-stop

Install `scripts/idle-stop/` on the EC2 instance. It is independent of this
desktop client.
