## Context

See `proposal.md` for motivation. The client is a PySide6 widget app: `LoginWindow` and `MainWindow` use default Qt layouts, a `QFormLayout` header that concatenates account ID and full ARN, an unstyled `QTableWidget`, a wrapping `QLabel` for the selection summary, stock `QPushButton`s, and a `QGroupBox` + `QPlainTextEdit` activity log. `QApplication` is created in `src/ec2_manager/main.py` with no Fusion style or stylesheet. Action enablement, feature flags, and confirmations already live in `state_logic` and `gui/dialogs.py`; this change must not move AWS work into widgets.

Constraints: Windows 10/11 is the customer runtime; Nuitka standalone must ship any new theme files; Linux CI has no trustworthy Windows GUI, so visual rules that need Qt widgets should be isolated behind helpers that unit tests can cover without a display where possible.

## Goals / Non-Goals

**Goals:**

- Centralize theming so login, main, table, and dialogs share one stylesheet and type scale.
- Restructure the main-window header and selection panel without changing which data is shown.
- Encode instance-state colors in one helper used by the table and the summary.
- Package theme files so source runs and the Nuitka build both resolve them.

**Non-Goals:**

- QML or a new GUI toolkit.
- Dark-mode toggle or per-profile themes.
- New AWS actions, columns, filters, or confirmation rules.
- Custom window chrome (frameless / client-side title bar).
- Accessibility overhaul beyond contrast that the theme already provides.

## Decisions

### 1. Keep PySide6 widgets; theme with Fusion + QSS

**Decision:** Stay on `QWidget` windows. At startup, set `QApplication` style to Fusion and load one application stylesheet.

**Rationale:** Fusion is consistent on Windows and in any Linux-side Qt tests. A single QSS file can restyle buttons, combos, tables, group boxes, and dialogs without rewriting layouts twice.

**Alternatives considered:**

- Native Windows style + light QSS — rejected; native controls fight custom padding and colors.
- Qt Quick / QML rewrite — rejected; out of scope and would redo working action/worker wiring.
- Per-widget `setStyleSheet` only — rejected; login, dialogs, and main would drift.

### 2. Theme module and packaged assets

**Decision:** Add `ec2_manager.gui.theme` that exposes `apply_theme(app: QApplication)` and path helpers. Put `theme.qss` and SVG (or PNG) icons under `src/ec2_manager/gui/assets/`. Register them in setuptools `package-data` and include the directory in the Nuitka Windows build.

**Rationale:** Importlib resources work in the source tree and in a packaged app. A `.qrc` compile step is extra toolchain for little gain.

**Alternatives considered:**

- Repo-root `assets/` only — rejected; installer already uses `assets/app.ico` for the exe icon; runtime theme files belong in the Python package.
- Qt `.qrc` — viable later if Nuitka resource discovery is painful; start with package data.

### 3. Header: two-row chrome, elided ARN

**Decision:** Replace the header `QFormLayout` with a toolbar-style row: profile name as title, account ID as a secondary badge, identity as an elided label with `setToolTip` (and accessible description) set to the full ARN, region combo, then Refresh and Logout. Keep all existing controls.

**Rationale:** Matches the spec (ARN available without crowding) without a new dialog or copy-to-clipboard feature.

**Alternatives considered:**

- Truncate ARN in place with no tooltip — rejected; operators still need the full principal.
- Separate “Identity” dialog — rejected; extra click for a string they already have.

### 4. State colors via a pure helper; table cells stay QTableWidgetItem

**Decision:** Add a small `instance_state_style(state: str) -> ...` helper (label + background/foreground) with no Qt types if practical, or only `QColor`. The State column sets item foreground/background (and optionally a rounded delegate if QSS cannot produce a pill). The selection panel reuses the same helper.

**Rationale:** Tests can lock the mapping (`running` vs `stopped` vs transitional vs `terminated`) in Docker without showing a window.

**Alternatives considered:**

- Custom `QStyledItemDelegate` only — extra code; use if flat cell colors look unfinished.
- CSS-like classes on a QML table — not applicable.

Color families (implementation may tune hex values for contrast):

| State | Family |
|---|---|
| `running` | green |
| `stopped` | red / muted red |
| `pending`, `stopping`, `rebooting`, `shutting-down` | amber |
| `terminated` | gray |
| unknown | neutral |

### 5. Action buttons: icons + object names for QSS

**Decision:** Set `objectName` values (`btnPrimary`, `btnDanger`, `btnSecondary`) and apply `QStyle.StandardPixmap` or packaged SVGs on Sign in, Refresh, Logout, Start, Stop, Restart, and Connect RDP. Do not change `is_action_enabled` / `is_action_visible` / RDP gating.

**Rationale:** QSS can target object names; enablement stays in existing logic. Standard pixmaps avoid new icon-license review; swap to bundled SVGs if standard icons look too system-like on Fusion.

**Alternatives considered:**

- Text-only restyle — fails the icon requirement.
- Emoji in button text — inconsistent fonts on Windows.

### 6. Selection panel as a QFrame card; activity log stays QPlainTextEdit

**Decision:** Put name, ID, state badge, type, and addresses in a `QFrame` with a grid or form that wraps cleanly. Keep Activity as a themed `QGroupBox` + read-only `QPlainTextEdit` (raise min height slightly; do not add timestamps unless messages already include them).

**Rationale:** Same data, scannable layout. Replacing the log with a list widget is unnecessary churn.

### 7. Dialogs pick up the application stylesheet

**Decision:** Keep `QMessageBox` helpers in `dialogs.py`. After `apply_theme`, Qt dialogs inherit the app stylesheet. If Fusion + QSS leaves message boxes looking native, parent them to the themed window and set the same style; do not rewrite confirmations as custom dialogs unless inheritance fails.

**Rationale:** Confirmation copy and Yes/No defaults must stay exactly as today.

## Risks / Trade-offs

- [QSS looks different under Nuitka / high-DPI] → Use Fusion, prefer `em`-like padding in px that we verify on 100% and 150% scaling; keep icons vector (SVG) where possible.
- [Standard Qt icons look dated next to a modern sheet] → Fall back to a small MIT-licensed SVG set in package assets; do not block the rest of the theme on that swap.
- [Nuitka omits `.qss` / icons] → Explicit `--include-data-dir` (or equivalent) in the Windows build workflow; add a startup log line if the stylesheet file is missing and still show a usable unstyled UI.
- [Linux CI cannot screenshot the GUI] → Unit-test state-color mapping and identity-shortening helpers; treat pixel polish as a Windows manual check.
- [Color-only state] → Always keep the state word; color is extra.

## Migration Plan

- No config, profile, or IAM migration.
- Existing operators install the next build; first launch shows the new theme with the same actions.
- Rollback is the previous installer; no data files to revert.

## Open Questions

None. Dark mode and a copy-ARN button can be a later change without altering this spec.
