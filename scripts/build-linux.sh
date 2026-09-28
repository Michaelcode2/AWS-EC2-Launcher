#!/usr/bin/env bash
# Build a standalone Linux AppImage with Nuitka (same compiler as Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(python3 - <<'PY'
import re
from pathlib import Path
text = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'(?m)^\s*version = "([^"]+)"', text)
if not match:
    raise SystemExit("Could not read project version from pyproject.toml")
print(match.group(1))
PY
)"
echo "Building EC2 Desktop Manager ${VERSION} (Linux AppImage)"

PYTHON="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTHON="${ROOT}/.venv/bin/python"
fi

install_deps() {
  if "${PYTHON}" -c "import nuitka, PySide6" >/dev/null 2>&1; then
    echo "Nuitka and PySide6 already available"
    return 0
  fi
  if command -v uv >/dev/null 2>&1; then
    uv pip install -e ".[dev]"
    return 0
  fi
  "${PYTHON}" -m pip install --upgrade pip
  "${PYTHON}" -m pip install -e ".[dev]"
}

install_deps

mkdir -p dist/nuitka dist/appimage
rm -rf dist/nuitka/main.dist dist/nuitka/main.build dist/appimage/AppDir
rm -f dist/EC2DesktopManager-*.AppImage

"${PYTHON}" -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --enable-plugin=pyside6 \
  --include-data-dir=config=config \
  --include-package-data=ec2_manager \
  --company-name="EC2 Desktop Manager" \
  --product-name="EC2 Desktop Manager" \
  --file-version="${VERSION}" \
  --product-version="${VERSION}" \
  --output-dir=dist/nuitka \
  --output-filename=Ec2DesktopManager \
  src/ec2_manager/main.py

DIST_DIR="dist/nuitka/main.dist"
if [[ ! -x "${DIST_DIR}/Ec2DesktopManager" ]]; then
  echo "Nuitka did not produce ${DIST_DIR}/Ec2DesktopManager" >&2
  exit 1
fi

# Copy non-glibc shared libraries for the binary and every bundled .so (Qt plugins
# are dlopen'd and do not appear on the main executable's NEEDED list alone).
python3 - <<'PY'
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

dist = Path("dist/nuitka/main.dist")
exclude_prefixes = (
    "libc.so",
    "libpthread.so",
    "libdl.so",
    "librt.so",
    "libresolv.so",
    "ld-linux",
    "linux-vdso",
)
lib_re = re.compile(r"=>\s+(\S+)\s+\(")


def is_excluded(path: Path) -> bool:
    name = path.name
    return any(name.startswith(prefix) for prefix in exclude_prefixes)


def ldd_paths(target: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["ldd", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    found: list[Path] = []
    for line in completed.stdout.splitlines():
        match = lib_re.search(line)
        if not match:
            continue
        path = Path(match.group(1))
        if path.is_file() and not is_excluded(path):
            found.append(path)
    return found


def copy_lib(lib: Path) -> bool:
    destination = dist / lib.name
    if destination.exists() or not lib.is_file():
        return False
    shutil.copy2(lib, destination)
    return True


# Qt/PySide often dlopen GL/EGL; they do not always appear in NEEDED via ldd.
extra_names = (
    "libEGL.so.1",
    "libGL.so.1",
    "libGLdispatch.so.0",
    "libGLX.so.0",
    "libOpenGL.so.0",
)
search_dirs = (
    Path("/usr/lib/x86_64-linux-gnu"),
    Path("/lib/x86_64-linux-gnu"),
    Path("/usr/lib64"),
    Path("/usr/lib"),
)
extra_copied = 0
missing_extras: list[str] = []
for name in extra_names:
    if (dist / name).is_file():
        continue
    found = False
    for directory in search_dirs:
        candidate = directory / name
        if not candidate.is_file():
            continue
        if copy_lib(candidate):
            extra_copied += 1
        found = True
        break
    if not found and name == "libEGL.so.1":
        missing_extras.append(name)
if missing_extras:
    raise SystemExit(
        "Required GL/EGL libraries were not found on the build host: "
        + ", ".join(missing_extras)
        + ". Install libegl1 (and related Mesa/GLVND packages) before building."
    )

targets = [dist / "Ec2DesktopManager", *sorted(dist.rglob("*.so*"))]
copied = 0
pending = list(targets)
seen: set[Path] = set()
while pending:
    target = pending.pop()
    if not target.is_file() or target in seen:
        continue
    seen.add(target)
    for lib in ldd_paths(target):
        if copy_lib(lib):
            copied += 1
            pending.append(dist / lib.name)
print(f"Copied {copied} ldd libraries and {extra_copied} GL/EGL libraries into {dist}")
PY

APPDIR="dist/appimage/AppDir"
mkdir -p "${APPDIR}/usr/bin"
# Keep Nuitka runtime files beside the binary (RPATH / relative lookups).
cp -a "${DIST_DIR}/." "${APPDIR}/usr/bin/"
cp assets/app.png "${APPDIR}/ec2-desktop-manager.png"
ln -sf ec2-desktop-manager.png "${APPDIR}/.DirIcon"

cat > "${APPDIR}/Ec2DesktopManager.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=EC2 Desktop Manager
Comment=Manage permitted Amazon EC2 instances
Exec=Ec2DesktopManager
Icon=ec2-desktop-manager
Categories=Network;Utility;
Terminal=false
EOF

cat > "${APPDIR}/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

install_desktop_entry() {
  local appimage="${APPIMAGE:-}"
  if [[ -z "${appimage}" ]]; then
    echo "APPIMAGE is not set. Launch the AppImage itself (not an extracted tree) to install a menu entry." >&2
    exit 1
  fi
  local apps="${HOME}/.local/share/applications"
  local icons="${HOME}/.local/share/icons/hicolor/256x256/apps"
  mkdir -p "${apps}" "${icons}"
  cp "${HERE}/ec2-desktop-manager.png" "${icons}/ec2-desktop-manager.png"
  cat > "${apps}/ec2-desktop-manager.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=EC2 Desktop Manager
Comment=Manage permitted Amazon EC2 instances
Exec=${appimage}
Icon=ec2-desktop-manager
Categories=Network;Utility;
Terminal=false
DESKTOP
  echo "Installed desktop entry at ${apps}/ec2-desktop-manager.desktop"
}

if [[ "${1:-}" == "--install-desktop-entry" ]]; then
  install_desktop_entry
  exit 0
fi

# Run from the Nuitka dist directory so relative Qt plugin lookups succeed.
cd "${HERE}/usr/bin"
export LD_LIBRARY_PATH="${HERE}/usr/bin${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
exec ./Ec2DesktopManager "$@"
EOF
chmod +x "${APPDIR}/AppRun"

ARCH="$(uname -m)"
case "${ARCH}" in
  x86_64|amd64) APPIMAGE_ARCH="x86_64" ;;
  aarch64|arm64) APPIMAGE_ARCH="aarch64" ;;
  *)
    echo "Unsupported architecture: ${ARCH}" >&2
    exit 1
    ;;
esac

TOOL_DIR="dist/appimage/tools"
mkdir -p "${TOOL_DIR}"
APPIMAGETOOL="${TOOL_DIR}/appimagetool-${APPIMAGE_ARCH}.AppImage"
if [[ ! -x "${APPIMAGETOOL}" ]]; then
  echo "Downloading appimagetool..."
  curl -fsSL \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage" \
    -o "${APPIMAGETOOL}"
  chmod +x "${APPIMAGETOOL}"
fi

OUT_NAME="EC2DesktopManager-${VERSION}-${APPIMAGE_ARCH}.AppImage"
OUT_PATH="dist/${OUT_NAME}"
rm -f "${OUT_PATH}"

# Avoid requiring FUSE on the build host.
export ARCH="${APPIMAGE_ARCH}"
APPIMAGE_EXTRACT_AND_RUN=1 "${APPIMAGETOOL}" "${APPDIR}" "${OUT_PATH}"
chmod +x "${OUT_PATH}"

echo "AppImage written to ${OUT_PATH}"
