## Why

Linux desktop operators on Ubuntu, KDE Plasma, and Linux Mint cannot use the shipped application. The GUI, AWS CLI lookup, and XDG config paths already run from source on Linux, but the only compiled product is a Windows installer, and Connect RDP always starts `mstsc.exe`.

## What Changes

- Add a compiled Linux desktop build so operators do not need Python, matching the Windows "no Python on the PC" promise.
- Publish that build from GitHub Actions as one x86_64 artifact that runs on Ubuntu Desktop, KDE Plasma, and Linux Mint without a per-desktop or per-distro package.
- On Linux, launch a FreeRDP client already installed on the machine (`xfreerdp`, `xfreerdp3`, or `wlfreerdp`) instead of `mstsc.exe`. Windows continues to launch `mstsc.exe`.
- On first Linux launch, create the existing per-user config directory and copy the example profile when the user has no profiles yet. The Windows installer keeps doing that copy itself.
- Leave inventory, actions, authentication, theming, and the on-instance idle-stop package unchanged.

Assumption: "Ubuntu core" means Ubuntu Desktop (the main GNOME edition), together with KDE Plasma and Linux Mint desktops. It does not mean Ubuntu Core, the snap-only OS.

## Capabilities

### New Capabilities

- `linux-distribution`: Nuitka standalone Linux build, single desktop artifact, GitHub Actions publish, first-run config seeding, and no secrets in the artifact. Operators on Ubuntu Desktop, KDE Plasma, and Linux Mint can launch the app without installing Python.

### Modified Capabilities

- `rdp-connect`: Connect RDP on Linux starts a host FreeRDP client against the same address selection as today. The Windows Remote Desktop client remains the Windows launch path. The application still must not store or inject a Windows password.

## Impact

- New Linux build script and workflow, parallel to `scripts/build-windows.ps1` and `.github/workflows/build-windows.yml`. Windows packaging stays in place.
- Small change in `src/ec2_manager/rdp/launcher.py` and its tests. Address selection, readiness checks, and the GUI stay as they are.
- First-run profile copy uses the existing XDG path in `src/ec2_manager/host/paths.py` (`$XDG_DATA_HOME/Ec2DesktopManager` or `~/.local/share/Ec2DesktopManager`).
- Linux operators still install AWS CLI v2 themselves (same requirement as Windows) and a FreeRDP package when they use Connect RDP. Those tools are not bundled.
- No change to IAM, EC2 API usage, profile TOML shape, or `scripts/idle-stop/`.
