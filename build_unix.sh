#!/usr/bin/env bash
# Build the VanishCam desktop app (onedir) for Linux/macOS with PyInstaller.
set -u
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv-build"
VENV_PY="$VENV_DIR/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "[Build] Creating the build Python environment..."
  "$PYTHON" -m venv "$VENV_DIR" || exit 1
fi

if ! "$VENV_PY" -c "import PyInstaller, cv2, mediapipe, numpy, pyvirtualcam, pygame, PySide6" >/dev/null 2>&1; then
  echo "[Build] Installing build dependencies..."
  "$VENV_PY" -m pip install --upgrade pip || exit 1
  "$VENV_PY" -m pip install -r requirements.txt "pyinstaller>=6,<7" || exit 1
fi

echo "[Build] Checking required MediaPipe models..."
"$VENV_PY" -c "from vanish_cam import download_models; download_models('normal'); download_models('goku')" || exit 1

echo "[Build] Running unit tests..."
"$VENV_PY" -m unittest discover || exit 1

echo "[Build] Checking resources..."
"$VENV_PY" vanish_cam.py --self-test || exit 1

"$VENV_PY" -m PyInstaller --noconfirm --distpath dist --workpath build VanishCam.spec || exit 1

BINARY="dist/VanishCam/VanishCam"
echo "[Build] Self-testing $BINARY..."
"$BINARY" --self-test || exit 1

echo "[Build] Preparing Linux AppDir..."
APPDIR="dist/VanishCam.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp -a dist/VanishCam/. "$APPDIR/usr/bin/"
cp packaging/vanishcam.desktop "$APPDIR/vanishcam.desktop"
cp assets/vanish_icon.ico "$APPDIR/vanishcam.ico"
if command -v convert >/dev/null 2>&1; then
  convert 'assets/vanish_icon.ico[5]' "$APPDIR/vanishcam.png" 2>/dev/null || true
fi
cp packaging/AppRun "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

if command -v appimagetool >/dev/null 2>&1; then
  echo "[Build] Creating AppImage..."
  appimagetool "$APPDIR" "dist/VanishCam.AppImage" || exit 1
else
  echo "[Build] appimagetool not found; AppDir is ready in $APPDIR"
fi

echo
echo "[Build] Ready in dist: VanishCam (onedir), VanishCam.AppDir, and AppImage when available"
