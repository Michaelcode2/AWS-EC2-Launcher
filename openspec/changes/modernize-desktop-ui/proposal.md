## Why

The main window still uses stock PySide6 widgets with a dense form header, a full IAM ARN, plain-text instance state, and unlabeled gray buttons. Operators need a clearer, more modern layout so they can see who they are, which instance is selected, and which actions are available without reading a wall of text.

## What Changes

- Restyle the login window, main window, instance table, and confirmation dialogs with a consistent modern theme (typography, spacing, color, and hover/disabled states).
- Reorganize the main-window header so profile name, account identity, region, Refresh, and Logout have a clear visual hierarchy; keep the full ARN available without crowding the header.
- Show instance state as a color-coded status (running, stopped, transitional, terminated) in the table and the selected-instance summary.
- Add icons and stronger primary/destructive styling to Start, Stop, Restart, Connect RDP, Refresh, Logout, and Sign in.
- Improve the selected-instance panel and Activity log so status is easier to scan.
- Keep existing AWS behavior, table columns, action enablement rules, feature flags, and confirmation policy unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `desktop-gui`: Presentation of the login and main windows, instance-state visibility, identity chrome, action affordances, and activity panel. Functional requirements (columns, enablement, confirmations, no in-app AWS password) stay in force.

## Impact

- GUI layer only: `src/ec2_manager/gui/` (windows, table, dialogs) and application startup in `src/ec2_manager/main.py` (theme/style application).
- Likely new theme assets (Qt stylesheet and optional icons) packaged with the Nuitka build.
- No AWS API, IAM, profile TOML, or idle-stop changes.
- No new runtime dependencies expected beyond PySide6 already in use.
- Linux unit tests that do not instantiate Qt remain valid; add GUI-safe tests where presentation helpers can run without a Windows display.
