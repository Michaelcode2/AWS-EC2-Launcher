#!/usr/bin/env bash
# Smoke-test a built AppImage under Xvfb: process must map a window, then exit.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

shopt -s nullglob
APPIMAGES=(dist/EC2DesktopManager-*.AppImage)
if [[ ${#APPIMAGES[@]} -eq 0 ]]; then
  echo "No AppImage found under dist/" >&2
  exit 1
fi
APPIMAGE="${APPIMAGES[0]}"

for cmd in xvfb-run xdotool; do
  if ! command -v "${cmd}" >/dev/null; then
    echo "${cmd} is required for the Linux AppImage smoke test" >&2
    exit 1
  fi
done

export APPIMAGE_EXTRACT_AND_RUN=1
export QT_QPA_PLATFORM=xcb

xvfb-run -a -s "-screen 0 1280x800x24" bash -c '
set -euo pipefail
APPIMAGE="$1"
LOG="$(mktemp)"
cleanup() {
  if [[ -n "${PID:-}" ]] && kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}" 2>/dev/null || true
    wait "${PID}" 2>/dev/null || true
  fi
  rm -f "${LOG}"
}
trap cleanup EXIT

"${APPIMAGE}" >"${LOG}" 2>&1 &
PID=$!

deadline=$((SECONDS + 90))
WINDOW_ID=""
while (( SECONDS < deadline )); do
  if ! kill -0 "${PID}" 2>/dev/null; then
    echo "AppImage exited before mapping a window. Log:" >&2
    cat "${LOG}" >&2 || true
    exit 1
  fi
  WINDOW_ID="$(xdotool search --name "EC2 Desktop Manager" 2>/dev/null | head -n 1 || true)"
  if [[ -z "${WINDOW_ID}" ]]; then
    WINDOW_ID="$(xdotool search --class "Ec2DesktopManager" 2>/dev/null | head -n 1 || true)"
  fi
  if [[ -n "${WINDOW_ID}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${WINDOW_ID}" ]]; then
  echo "Timed out waiting for an application window. Log:" >&2
  cat "${LOG}" >&2 || true
  exit 1
fi

echo "Mapped window ${WINDOW_ID}; terminating AppImage"
kill "${PID}" 2>/dev/null || true
wait "${PID}" 2>/dev/null || true
echo "Linux AppImage smoke test passed"
' bash "${APPIMAGE}"
