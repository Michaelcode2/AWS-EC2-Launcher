## 1. Remote Desktop client selection

- [x] 1.1 Add a pure RDP command builder that returns `mstsc.exe /v:<address>` on `win32` and the first of `xfreerdp`, `xfreerdp3`, `wlfreerdp` on any other platform, and verify unit tests cover that order, a missing client error naming `freerdp2-x11` and `freerdp3-x11`, and the absence of a password argument
- [x] 1.2 Call that builder from `launch_rdp` without changing address selection or the TCP readiness check, and verify the existing launch test passes on Linux by asserting the Windows command and the Linux command as separate cases

## 2. First-run configuration

- [x] 2.1 Treat a Nuitka-compiled module like a frozen build in `bundled_config_dir` so the bundled `config` directory is the one next to the executable, and verify a unit test for the compiled path and the existing source-tree path
- [x] 2.2 On startup, create the per-user config directory and copy `example-profile.toml` only when that directory has no TOML files, and verify a unit test that an empty directory receives the example and an existing profile is not overwritten
- [x] 2.3 Invoke that helper before profiles are loaded, and verify the startup path calls it by a unit test or a direct assertion on the helper's result

## 3. Linux AppImage

- [x] 3.1 Add `assets/app.png` derived from `assets/app.ico` for the desktop entry, and verify the PNG file exists in the repo
- [x] 3.2 Add `scripts/build-linux.sh` that runs the same Nuitka standalone flags as the Windows build without the `--windows-*` flags, copies non-glibc `ldd` dependencies of the binary and every bundled `.so` (excluding libc, libpthread, libdl, librt, libresolv, and the dynamic linker), and packs one `dist/EC2DesktopManager-*.AppImage`, and verify a local run of the script produces that file
- [x] 3.3 Teach `AppRun` to handle `--install-desktop-entry` by writing a per-user desktop file and icon under the home directory, and verify running it with that flag creates `~/.local/share/applications/ec2-desktop-manager.desktop` whose `Exec` points at the AppImage and does not require root
- [x] 3.4 Confirm the AppImage contains `libqxcb.so` and `libqwayland.so` and does not contain the AWS CLI or a FreeRDP client, and verify by listing those paths inside the extracted AppImage

## 4. GitHub Actions

- [x] 4.1 Add `.github/workflows/build-linux.yml` as `workflow_dispatch` on `ubuntu-22.04`, leaving `build-windows.yml` and the `test` workflow unchanged, and verify the workflow file pins `ubuntu-22.04`
- [x] 4.2 In that workflow, smoke-test the AppImage with `APPIMAGE_EXTRACT_AND_RUN=1` under Xvfb so the process maps a window, and verify the workflow fails if the process exits before a window is mapped
- [x] 4.3 Run `scripts/check_artifacts.py` on `dist` and `config`, upload `ec2-desktop-manager-linux`, and verify the workflow publishes only the AppImage

## 5. Operator documentation

- [x] 5.1 Document the Linux artifact in the README: no Python required, supported desktops (Ubuntu Desktop 22.04/24.04, KDE Plasma on those bases, Linux Mint 21/22), AWS CLI v2 and FreeRDP as host packages, `libfuse2` / `libfuse2t64` or `APPIMAGE_EXTRACT_AND_RUN=1`, and `./scripts/build-linux.sh`, and verify those points are present in the README
