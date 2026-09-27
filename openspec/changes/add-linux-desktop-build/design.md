## Context

The shipped product is a Nuitka standalone tree wrapped by Inno Setup (see `scripts/build-windows.ps1`). PySide6, Boto3, XDG config paths (`user_data_dir`), and AWS CLI discovery (`shutil.which("aws")`) already work on Linux. Connect RDP is hardcoded to `mstsc.exe` in `src/ec2_manager/rdp/launcher.py`. The Windows installer, not the app, copies `config/example-profile.toml` into the per-user config directory. Nuitka does not set `sys.frozen`, so `bundled_config_dir()` still points at the source tree unless the process is a PyInstaller build.

See proposal.md for why a Linux desktop build is in scope. Requirements live in `specs/linux-distribution/spec.md` and `specs/rdp-connect/spec.md`.

## Goals / Non-Goals

**Goals:**

- Reuse the Windows Nuitka standalone invocation, minus Windows-only flags, and wrap it as one AppImage.
- Keep application code changes limited to RDP command selection, bundled-config detection, and first-run profile copy.
- Build on Ubuntu 22.04 so the glibc baseline covers Ubuntu 22.04/24.04, KDE Plasma on those bases, and Linux Mint 21/22.
- Prove the GUI process starts under Xvfb in CI.

**Non-Goals:**

- Debian packages, Flatpak, Snap, or a PyInstaller build.
- Ubuntu Core (snap-only) and any desktop older than Ubuntu 22.04 / Mint 21.
- arm64, per-desktop themes, bundling AWS CLI or FreeRDP, code signing, and changes to `scripts/idle-stop/` or the Windows installer.
- Replacing the custom Qt stylesheet with the host desktop theme.

## Decisions

### 1. Nuitka standalone, then AppImage

Keep `--standalone --enable-plugin=pyside6 --include-data-dir=config=config --include-package-data=ec2_manager` and drop `--windows-*` flags. Output filename `Ec2DesktopManager`. Pack that directory as an AppImage with the official `appimagetool` downloaded in the build script (same pattern as CI installing Inno Setup). Commit `assets/app.png` (produced from `assets/app.ico`) for the desktop entry; do not add ImageMagick or Pillow as project dependencies.

AppDir layout: the Nuitka dist contents live next to each other under `usr/bin` (the binary needs its libraries beside it), with `Ec2DesktopManager.desktop` and the icon at the AppDir root and an `AppRun` that execs the binary.

Alternatives considered:

- **`.deb`**: native on Ubuntu and Mint, but a second packaging system and no gain for KDE Plasma versus GNOME or Cinnamon. The app already ships its own Qt theme, so a distro package does not improve the UI.
- **Flatpak or Snap**: sandbox rules for `~/.aws`, the browser SSO flow, and spawning a host `xfreerdp` are larger than the feature. Snap would only be required for Ubuntu Core, which this change does not target.
- **PyInstaller**: a second bundler beside Nuitka.
- **Nuitka onefile**: worse startup and harder Qt plugin failures. Windows already ships standalone-inside-an-installer; Linux mirrors that with standalone-inside-an-AppImage.
- **Source install only**: does not meet the no-Python requirement.

### 2. Build host is `ubuntu-22.04`

Pin the GitHub Actions runner to `ubuntu-22.04` (glibc 2.35). `ubuntu-latest` is newer and the resulting binary would fail on Ubuntu 22.04 and Linux Mint 21. Do not retarget the existing `test` workflow; unit tests stay on `ubuntu-latest`.

After Nuitka, copy non-glibc shared libraries reported by `ldd` for the executable and for every `.so` in the dist (including Qt platform plugins) into the dist. Exclude libc, libpthread, libdl, librt, libresolv, and the dynamic linker so the 22.04 glibc floor stays intact. Qt plugins are loaded with `dlopen`, so walking only the main executable is not enough.

CI smoke test: `APPIMAGE_EXTRACT_AND_RUN=1 xvfb-run` the AppImage and require the process to stay up long enough to map a window, then terminate it. That catches a missing `xcb` plugin without a desktop session. Wayland is not available on the runner; the pyside6 plugin must still ship `libqwayland.so` next to `libqxcb.so`, and a Wayland session is a manual check on a supported desktop.

FUSE: type-2 AppImages need `libfuse2` on Ubuntu 22.04+ and current Mint. The smoke test uses extract-and-run so CI does not depend on FUSE. The README must tell operators to install `libfuse2` (package name `libfuse2` or `libfuse2t64` on newer Ubuntu) or to launch with `APPIMAGE_EXTRACT_AND_RUN=1`.

### 3. Desktop entry travels inside the AppImage

`AppRun` handles `--install-desktop-entry` before starting Qt. It writes `~/.local/share/applications/ec2-desktop-manager.desktop` whose `Exec` is the absolute path of the AppImage, and copies the icon under `~/.local/share/icons/`. No root, no extra files in the Actions artifact.

File-manager launch is the AppImage itself (executable bit set). Dolphin, Nautilus, and Nemo all open an executable AppImage.

### 4. RDP command is chosen by platform, not by desktop

Add a pure function, called by `launch_rdp`, that takes the address, a platform string, and a PATH lookup:

- `win32` → `["mstsc.exe", "/v:<address>"]`
- otherwise → the first of `xfreerdp`, `xfreerdp3`, `wlfreerdp` that the lookup finds, with the same `/v:<address>` argument
- none found → raise an error whose message says to install FreeRDP (`freerdp2-x11` or `freerdp3-x11`)

Do not pass `/u`, `/p`, or any password flag. `main_window._connect_rdp` already surfaces exceptions in the activity log, so a missing client needs no new dialog. Address selection and the TCP readiness check stay as they are.

Tests must pass the platform in, so the Linux CI job still asserts the Windows command and also asserts the Linux search order. The current test calls `launch_rdp` and expects `mstsc.exe` on every OS; that assertion moves to the Windows case.

KDE's KRDC and GNOME/Mint Remmina are not called. One FreeRDP argv works on all three desktops and avoids per-desktop code.

### 5. First-run profile copy lives in the app

On startup, create `user_config_dir()` and, when it contains no `*.toml`, copy `bundled_config_dir() / "example-profile.toml"` into it. Treat Nuitka the same as a frozen build: `bundled_config_dir()` uses the directory of `sys.executable` when `sys.frozen` is set or when the module was compiled (`__compiled__` in that module). Source checkouts keep the current repo-relative path.

The Windows installer still copies the example profile. When that file is already present, the app copy does nothing. Running the helper on Windows is intentional: one code path, no AppImage install hook.

### 6. Workflow shape matches Windows

Add `.github/workflows/build-linux.yml` as `workflow_dispatch` only, parallel to `build-windows.yml`. Script: `scripts/build-linux.sh`. Artifact name `ec2-desktop-manager-linux`, path `dist/EC2DesktopManager-*.AppImage`. Reuse `scripts/check_artifacts.py` on `dist` and `config`. No signing step.

Local Linux build is `./scripts/build-linux.sh` from the repo root, with the same Nuitka flags as CI. Document the system packages the script needs (a C compiler, patchelf, and the Qt/X11 libraries Nuitka's plugin links) in the README, not as a new dependency in `pyproject.toml`. Nuitka is already in the `dev` extra.

## Risks / Trade-offs

- [AppImage FUSE is missing on a fresh Ubuntu or Mint install] → Document `libfuse2` / `libfuse2t64` and `APPIMAGE_EXTRACT_AND_RUN=1`. CI uses extract-and-run.
- [Qt plugin loads on Xvfb but fails on a Wayland-only session] → Ship the wayland platform plugin beside xcb. Confirm once on a Wayland Ubuntu or KDE session before calling the change done. Mint Cinnamon (X11) is covered by the xcb smoke test plus a manual X11 launch.
- [Copied host libraries accidentally include a newer glibc symbol] → Copy only libraries that are not in the glibc exclude list, and build only on 22.04. Do not switch the runner to `ubuntu-latest`.
- [`ldd` misses a dlopen dependency that is not under the dist yet] → The Xvfb smoke test fails the job if the xcb plugin cannot load. Add any newly discovered library to the copy step rather than documenting a long apt list for operators.
- [FreeRDP package names differ across Ubuntu 22.04, 24.04, and Mint] → Resolve `xfreerdp`, then `xfreerdp3`, then `wlfreerdp` on `PATH`. The error names both apt packages.
- [First-run copy also runs on Windows] → It no-ops when a profile already exists, which is the installer outcome. It does not change the installer script.

## Migration Plan

No data migration. Existing Windows installs are unchanged. Linux operators gain a new artifact; they do not have an older Linux install to replace.

Rollback is to stop publishing `build-linux` artifacts. The RDP and first-run changes are safe on Windows: the Windows command stays `mstsc.exe`, and profile copy does not overwrite an existing TOML file. Reverting those commits restores the previous Linux-from-source behavior (`mstsc.exe`, which already fails on Linux).

## Open Questions

None. The desktop set is Ubuntu Desktop, KDE Plasma, and Linux Mint, not Ubuntu Core. A Snap build would be a separate change if Ubuntu Core becomes a target.
