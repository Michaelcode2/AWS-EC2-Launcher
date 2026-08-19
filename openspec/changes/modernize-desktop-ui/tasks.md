## 1. Theme infrastructure

- [x] 1.1 Add `src/ec2_manager/gui/assets/theme.qss` with Fusion-friendly styles for windows, labels, combos, tables, group boxes, text edits, and `btnPrimary` / `btnDanger` / `btnSecondary` buttons (including disabled and hover)
- [x] 1.2 Add `ec2_manager.gui.theme` with `apply_theme(app)` that sets Fusion, loads the QSS via importlib resources, and logs a warning without crashing if the stylesheet is missing
- [x] 1.3 Register `gui/assets/*` in setuptools `package-data` and include those files in `scripts/build-windows.ps1` Nuitka data
- [x] 1.4 Call `apply_theme` from `main.py` immediately after creating `QApplication`, before login or configuration-error dialogs

## 2. Presentation helpers

- [x] 2.1 Add a Qt-free helper that maps instance state to a family (`running`, `stopped`, `transitional`, `terminated`, `unknown`) plus foreground/background color strings used by the table and summary
- [x] 2.2 Add a Qt-free helper that shortens an IAM ARN for header display while preserving the original string for tooltip/accessible text
- [x] 2.3 Add unit tests for state-family mapping and ARN shortening covering running, stopped, transitional, terminated, unknown, and a typical user/role ARN

## 3. Login and action affordances

- [x] 3.1 Restyle `LoginWindow` layout (profile selector, helper text, primary Sign in) and set the Sign in object name plus icon
- [x] 3.2 Apply icons and object names on Refresh, Logout, Start, Stop, Restart, and Connect RDP without changing enablement, visibility, or confirmation behavior

## 4. Main window layout

- [x] 4.1 Replace the main-window `QFormLayout` header with toolbar chrome: profile title, account badge, elided identity with full-ARN tooltip, region combo, Refresh, Logout
- [x] 4.2 Color the instance table State column from the shared helper while keeping existing columns and selection behavior
- [x] 4.3 Replace the wrapping details `QLabel` with a `QFrame` summary panel (name, ID, state badge, type, addresses, empty-state copy) that reuses the same state helper
- [x] 4.4 Theme the Activity group box and log so it is visually distinct from the table; keep append-only session messages including the initial signed-in line

## 5. Verification

- [x] 5.1 Confirm existing state-logic, action, and RDP tests still pass and that ruff/mypy succeed
- [ ] 5.2 Manually verify on Windows: login and main share the theme, Stop/Restart confirmations look themed, stopped vs running state colors, header tooltip shows the full ARN, and disabled action buttons stay distinct
