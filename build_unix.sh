#!/usr/bin/env bash
# Build VanishCam packaged binaries for Linux/macOS with PyInstaller.
# Windows builds use BUILD_WINDOWS.bat.
set -u
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv-build"
VENV_PY="$VENV_DIR/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "[Build] Creating the build Python environment..."
  "$PYTHON" -m venv "$VENV_DIR" || exit 1
fi

if ! "$VENV_PY" -c "import PyInstaller, cv2, mediapipe, numpy, pyvirtualcam, pygame" >/dev/null 2>&1; then
  echo "[Build] Installing build dependencies..."
  "$VENV_PY" -m pip install --upgrade pip || exit 1
  "$VENV_PY" -m pip install -r requirements.txt "pyinstaller>=6,<7" || exit 1
fi

echo "[Build] Checking required MediaPipe models..."
"$VENV_PY" -c "from vanish_cam import download_models; download_models('normal'); download_models('goku')" || exit 1

"$VENV_PY" -m PyInstaller --noconfirm --distpath dist --workpath build VanishCam.spec || exit 1

for binary in \
  "dist/VanishCam" \
  "dist/Naruto Vanish Effect" \
  "dist/Goku Vanish Effect" \
  "dist/Normal and Particles Vanish"; do
  if [[ -x "$binary" ]]; then
    echo "[Build] Self-testing $binary..."
    "$binary" --self-test || exit 1
  else
    echo "[Build] Missing built binary: $binary"
    exit 1
  fi
done

echo
echo "[Build] Ready in dist: VanishCam, Naruto Vanish Effect, Goku Vanish Effect, Normal and Particles Vanish"
