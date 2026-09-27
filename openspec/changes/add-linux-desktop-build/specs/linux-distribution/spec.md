## Purpose

Produces one compiled Linux desktop application that Ubuntu Desktop, KDE Plasma, and Linux Mint operators can launch without installing Python.

## ADDED Requirements

### Requirement: Standalone Linux application
The distributed Linux application SHALL run on a supported desktop without requiring Python to be installed. Supported desktops are Ubuntu Desktop 22.04 and 24.04, KDE Plasma on those Ubuntu bases, and Linux Mint 21 and 22, all x86_64.

#### Scenario: Launch without Python
- **WHEN** an operator launches the distributed application on a supported desktop that does not have Python installed
- **THEN** the application starts and presents the login/profile flow

#### Scenario: Same build on each supported desktop
- **WHEN** the same published artifact is launched on Ubuntu Desktop, on KDE Plasma, and on Linux Mint
- **THEN** each desktop presents the login/profile flow from that artifact

### Requirement: Desktop launch without administrator rights
The distributed application SHALL be launchable from the file manager on the supported desktops. It SHALL also be possible to add an application-menu launcher and icon for the current user without administrator rights.

#### Scenario: File manager launch
- **WHEN** the operator opens the published artifact from the file manager on a supported desktop
- **THEN** the application starts

#### Scenario: Per-user menu launcher
- **WHEN** the operator asks the application to install its menu launcher
- **THEN** a launcher appears for that user without writing outside the user account and without administrator rights

### Requirement: X11 and Wayland sessions
The application window SHALL appear in an X11 session and in a Wayland session on the supported desktops.

#### Scenario: X11 session
- **WHEN** the operator launches the application in an X11 session
- **THEN** the login window is shown

#### Scenario: Wayland session
- **WHEN** the operator launches the application in a Wayland session
- **THEN** the login window is shown

### Requirement: First-run configuration directory
On Linux, the first launch SHALL create the per-user configuration directory at `$XDG_DATA_HOME/Ec2DesktopManager/config` when `XDG_DATA_HOME` is set, otherwise at `~/.local/share/Ec2DesktopManager/config`. When that directory contains no profile files, the application SHALL copy the shipped example profile into it. Existing profile files MUST NOT be overwritten.

#### Scenario: Empty config directory
- **WHEN** the operator launches the Linux application and the per-user config directory has no TOML profiles
- **THEN** the directory exists and contains the example profile

#### Scenario: Existing profiles are kept
- **WHEN** the operator launches the Linux application and the per-user config directory already contains a TOML profile
- **THEN** that profile is left unchanged

### Requirement: GitHub Actions Linux compile
A GitHub Actions workflow SHALL compile the Linux application on an x86_64 Linux runner and publish the desktop artifact. The workflow MUST NOT embed AWS keys, Windows passwords, signing private keys, or SSO tokens.

#### Scenario: Workflow produces an artifact
- **WHEN** the Linux build workflow runs
- **THEN** it publishes one Linux desktop artifact and that artifact contains no credentials or private keys

### Requirement: Host tools stay outside the application
The Linux application MUST NOT bundle AWS CLI or a Remote Desktop client. Sign-in continues to use an AWS CLI v2 the operator installed. Connect RDP continues to use a Remote Desktop client the operator installed.

#### Scenario: AWS CLI is not inside the artifact
- **WHEN** the published Linux artifact is inspected
- **THEN** it does not contain the AWS CLI or a Remote Desktop client
