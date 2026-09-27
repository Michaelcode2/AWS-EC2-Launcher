# EC2 Desktop Manager

Desktop client for listing, starting, stopping, restarting, and opening RDP to
Amazon EC2 instances the signed-in principal is allowed to manage. Distributed
builds exist for Windows (installer) and Linux (AppImage).

**IAM remains the authorization boundary.** This application improves
usability. A local configuration file cannot grant access that AWS denies.
Customers do **not** need Python on their PCs; GitHub Actions produces a
standalone Windows installer and a Linux AppImage.

## Features

- Sign-in with an AWS CLI named profile (IAM user access keys or IAM Identity Center)
- Account ID check with STS before the main window opens
- Paginated instance inventory with tag or instance-ID filters
- Start / Stop / Restart with confirmation and polling
- Elastic IP display and platform RDP launch (`mstsc.exe` on Windows, FreeRDP on Linux)
- Optional on-instance idle auto-stop (separate package)

## Develop on Linux

Unit tests and linters run on Linux (locally or in Docker). The GUI can also
be started from source for layout work. Ship a compiled AppImage for operators
who do not have Python.

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

## Linux AppImage

GitHub Actions workflow `build-linux` runs on `ubuntu-22.04`, compiles with
Nuitka, packs a single x86_64 AppImage, smoke-tests it under Xvfb, and uploads
the artifact. Download it from the workflow run.

Supported desktops (x86_64):

- Ubuntu Desktop 22.04 and 24.04
- KDE Plasma on those Ubuntu bases
- Linux Mint 21 and 22

Operators still install **AWS CLI v2** for sign-in and a **FreeRDP** client for
Connect RDP (`freerdp2-x11` or `freerdp3-x11`). Those tools are not inside the
AppImage.

Type-2 AppImages need FUSE 2 on the host. Install `libfuse2` (or `libfuse2t64`
on newer Ubuntu) or launch with:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./EC2DesktopManager-*.AppImage
```

Optional per-user application menu entry (no root):

```bash
./EC2DesktopManager-*.AppImage --install-desktop-entry
```

Profiles are stored under `~/.local/share/Ec2DesktopManager/config/` (or
`$XDG_DATA_HOME/Ec2DesktopManager/config/`).

On a Linux machine you can also build locally:

```bash
./scripts/build-linux.sh
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

See `docs/onboarding.md` (Windows) or `docs/onboarding-linux.md` (Linux), and
`config/example-profile.toml`. Profiles live in
`%LOCALAPPDATA%\Ec2DesktopManager\config\` on Windows and
`~/.local/share/Ec2DesktopManager/config/` on Linux after first launch.

## Idle auto-stop

Install `scripts/idle-stop/` on the EC2 instance. It is independent of this
desktop client.
