<div align="center">
 <h1>VanishCam</h1>
</div>
<div align="center">
<img width="200" height="200" alt="vanishcam_minimal_logo" src="https://github.com/user-attachments/assets/daa06215-cb7e-4ae5-97c3-77ad3b2458b5" />
</div>

> [!WARNING]
> **Under construction** — this release contains the desktop-app rewrite: a Qt
> launcher and preview window, one packaged binary instead of four editions,
> persisted settings, and installers. It is still being tested and may change.

VanishCam adds animated disappearance effects to a live webcam feed. Webcam
frames are processed on your computer and are not recorded or uploaded by this
app. Packaged builds also check licenses online; see [Privacy and network use](#privacy-and-network-use).

## Requirements

- Windows 10/11, Linux, or macOS (Intel or Apple silicon) and a working webcam
- **Python 3.10–3.13** for source runs and builds. Packaged apps bundle their
  own runtime, so no Python is needed for them. Python 3.14 is not supported
  yet: pygame 2.6 has no 3.14 wheel and its source build fails on current
  setuptools.
- Internet access the first time dependencies and MediaPipe models are downloaded
- Optional: OBS Studio with its Virtual Camera driver for calls/streams on
  Windows, or the `v4l2loopback` kernel module on Linux, for virtual camera output

Good lighting and a still camera matter more than raw resolution. VanishCam
captures an empty view of your room as the background first, so keep the area
behind you uncluttered and free of movement.

## Install and start

### Windows

Download `VanishCamSetup.exe` from the releases page and run it. The installer
is per-user (no administrator rights needed), adds a Start menu entry and an
optional desktop icon, and includes an uninstaller. On first launch, enter the
email address for your license: packaged Windows builds check it online. No
Python installation is required.

For a source run, use the launchers from a PowerShell window in the project
folder — they create `.venv-local`, install dependencies on first run and pick
the newest installed Python from 3.13 down to 3.10:

```powershell
.\RUN_LOCAL.bat       # CLI with preview; accepts the options below
.\RUN_VIRTUAL.bat     # requires OBS Virtual Camera output
.\RUN_OBS.bat         # preview only, for an OBS Window Capture setup
```

### Linux / macOS

Download `VanishCam.AppImage`, make it executable and run it:

```bash
chmod +x VanishCam.AppImage
./VanishCam.AppImage
```

If an AppImage is unavailable, use the `VanishCam.AppDir` folder from the
release archive and run its `AppRun` script. Packaged Linux/macOS builds skip
license checks. For virtual camera output on Linux, load v4l2loopback first
(`sudo modprobe v4l2loopback`); otherwise use the preview window with an OBS
Window Capture source.

For a source run, the launchers create `.venv-local` and install dependencies
on first run:

```bash
./run_local.sh        # Qt desktop app (launcher + preview window)
./run_virtual.sh      # requires v4l2loopback output
./run_obs.sh          # preview only, for an OBS Window Capture setup
```

### Manual source setup

Use this if you prefer to manage the environment yourself. Pick any installed
Python 3.10–3.13:

```powershell
# Windows (PowerShell) — replace -3.12 with your installed version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe desktop.py          # Qt desktop app
# or: .\.venv\Scripts\python.exe vanish_cam.py --mode goku   # CLI
```

```bash
# Linux / macOS
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python desktop.py                    # Qt desktop app
# or: .venv/bin/python vanish_cam.py --mode goku           # CLI
```

Source runs never perform an online license check.

## Getting good results

1. **Start the app.** The Qt desktop app remembers your settings: pick an
   effect, check the camera preview, then click **Start effect**. CLI users
   select the effect with `--mode` instead. The packaged Windows build asks
   for your license email once before the launcher opens.
2. **Step out of frame for about four seconds** while VanishCam captures the
   empty room. A countdown banner appears on the preview during this step;
   return when it says the background was captured.
3. **Perform the gesture** for your effect. Keep your whole hand inside the
   frame and use even, front-facing light.
4. **Press `Space` to recapture** the background whenever the camera or room
   changes — a chair moved, the lights changed, someone walked behind you.
5. **Press `Q` or `Esc`** to quit and release the camera and virtual device.

Resolution defaults to the highest common size your camera supports while
preserving its aspect ratio. If the effect is slow, start at 1280x720 or lower.

For scripted use, `vanish_cam.py` keeps its command-line interface on both
platforms:

```powershell
# Windows
.\.venv\Scripts\python.exe vanish_cam.py --mode goku --no-virtual-camera
```

```bash
# Linux / macOS
.venv/bin/python vanish_cam.py --mode goku --no-virtual-camera
```

The Windows `RUN_*.bat` launchers forward extra arguments to this CLI. The
Linux/macOS `run_*.sh` launchers start the Qt desktop app, which ignores CLI
arguments — call `vanish_cam.py` directly when you need flags.

## Effects and gestures

- **Normal Vanish:** Raise your index and middle fingers in a V sign. Your
  silhouette dissolves. Press `R` to return.
- **Naruto Vanish:** Bring both palms together in front of you, fingers side by
  side rather than interlaced. Smoke and a falling log appear. Press `R` to
  return.
- **Particles:** Make the V sign. Your silhouette breaks into drifting colored
  fragments. Press `R` to return.
- **Goku:** Hold your straight, joined index and middle fingers against your
  forehead. The default hold time is three seconds; the app asks for a different
  duration when this mode starts. Repeat the gesture to reappear.
- **Itachi:** Touch both hands together in front of your chest. Your silhouette
  turns into crows. Touch your hands together again to return.
- **Infinity Gauntlet:** Show one hand to the camera. The drawn gauntlet follows
  your hand. Touch your thumb and middle fingertip, then snap them apart with a
  quick movement. After a three-second delay, your silhouette turns into cosmic
  dust. Press `R` to return.

Keep the hand fully inside the camera frame. In Goku and Infinity Gauntlet
modes, the gesture controls the effect; the `V` shortcut is disabled.

## Keyboard controls

The effect window has matching buttons; shortcuts work while it has focus.

| Key | Action |
| --- | --- |
| `Space` | Capture the empty background again; leave the frame while it captures. |
| `R` | Return to the camera view (mode-specific gesture behavior applies). |
| `V` | Start the effect manually where supported. |
| `F` | Toggle fullscreen. |
| `Q` or `Esc` | Quit and release the camera. |

## Use with a virtual camera

VanishCam automatically uses OBS Virtual Camera when it is available. In your
call or streaming app, select **OBS Virtual Camera** as the camera and keep
VanishCam running.

- **Windows:** install OBS Studio and click **Start Virtual Camera** in OBS
  first. Unity Capture is an alternative: `--virtual-backend unitycapture`.
- **Linux:** load the loopback module and select that backend:

  ```bash
  sudo modprobe v4l2loopback
  .venv/bin/python vanish_cam.py --virtual-camera --virtual-backend v4l2loopback
  ```

- **macOS:** no virtual camera backend is supported. Run with
  `--no-virtual-camera` and capture the **Webcam Preview** window with an OBS
  Window Capture source.

Use `RUN_VIRTUAL.bat` / `./run_virtual.sh` to require virtual camera output, or
`RUN_OBS.bat` / `./run_obs.sh` for preview-only operation with an OBS Window
Capture source (select the **Webcam Preview** window in OBS). Only one app can
provide virtual camera output at a time. Sound effects play through your
computer's audio output; virtual camera video does not include sound.

## Camera options

Choose a specific camera by index, or set a resolution and virtual output frame
rate. Specify both width and height together. For example:

```powershell
# Windows
.\.venv\Scripts\python.exe vanish_cam.py --camera 1 --width 1280 --height 720 --fps 30
```

```bash
# Linux / macOS
.venv/bin/python vanish_cam.py --camera 1 --width 1280 --height 720 --fps 30
```

The preview preserves the camera's aspect ratio instead of stretching the image.
For gesture troubleshooting, add `--gesture-debug`; diagnostics appear in the
terminal, not over the video.

## Launchers and build

| Platform | Launchers | What they start |
| --- | --- | --- |
| Windows | `RUN_LOCAL.bat`, `RUN_VIRTUAL.bat`, `RUN_OBS.bat` | CLI (`vanish_cam.py`) — extra arguments are forwarded |
| Linux/macOS | `run_local.sh`, `run_virtual.sh`, `run_obs.sh` | Qt desktop app (`desktop.py`) — CLI arguments are ignored |

Every launcher creates `.venv-local`, installs dependencies on first run and
selects a supported Python automatically. For example, on Windows:

```powershell
.\RUN_LOCAL.bat --mode infinity
```

On Linux/macOS, call the CLI directly when you need flags:

```bash
.venv/bin/python vanish_cam.py --mode infinity
```

To build the packaged app, run `BUILD_WINDOWS.bat` on Windows or `./build_unix.sh`
on Linux/macOS with Python 3.10–3.13 installed:

```powershell
# Windows
.\BUILD_WINDOWS.bat
```

```bash
# Linux / macOS
./build_unix.sh
```

Both scripts create an isolated `.venv-build`, download the MediaPipe models,
run the unit tests plus a resource self-test, and produce a single onedir app in
`dist/VanishCam` (Windows: `dist\VanishCam\VanishCam.exe`).

- **Windows:** if Inno Setup is installed and `ISCC` is on your PATH, the build
  also produces `dist\VanishCamSetup.exe`; otherwise it skips the installer.
- **Linux:** if `appimagetool` is available it also produces
  `dist/VanishCam.AppImage`; otherwise the `dist/VanishCam.AppDir` folder is
  ready to run via its `AppRun` script.
- Packaged Windows builds activate a license online; packaged Linux/macOS
  builds skip license checks, as do all source runs.

## Troubleshooting

- **Camera not found:** Close other apps using the webcam, check your operating
  system's camera permissions, and try another camera in the selection screen.
- **Effect does not trigger:** Improve the lighting, keep your full hand in the
  frame, and perform the gesture clearly.
- **Background looks wrong:** Press `Space`, leave the frame for the full
  capture, and keep the camera still.
- **Virtual camera unavailable:** On Windows, install OBS Studio and start its
  Virtual Camera; make sure no other app is using the output. On Linux, load
  `v4l2loopback`. On macOS, use an OBS Window Capture source instead.
- **Video is slow:** Try a smaller resolution, such as `--width 640 --height 360`.
- **No sound:** VanishCam falls back to `ffplay` if pygame's mixer is
  unavailable. Install ffmpeg (which provides ffplay), or use Python 3.10–3.13
  for built-in playback. Python 3.14 is not supported by pygame 2.6.
- **Build fails with a pygame wheel error or "No module named distutils":**
  you are on Python 3.14. Install Python 3.13 or older; the launchers and build
  scripts will select it automatically.
- **No installer on Windows:** `ISCC` (the Inno Setup compiler) must be on your
  PATH. The `dist\VanishCam` application itself is still complete.
- **Build reports missing MediaPipe models:** rerun the build while online; the
  models are downloaded to the user data directory on the first build.
- **AppImage does not start on Linux:** install FUSE (`libfuse2`), or run
  `dist/VanishCam.AppDir/AppRun` directly.

## Privacy and network use

The effects process the live camera feed locally. VanishCam does not send
webcam frames or captured backgrounds to its license service. The Python source
run directly with Python does not require an online license check. Packaged
Windows builds use Firebase for license activation and session checks; these
checks send the license email, an anonymous account identifier, a hashed device
identifier, and session information. Packaged builds on Linux and macOS skip
license checks entirely. Package installation may also contact
package repositories to download dependencies. Other camera, streaming, or
video-call software has its own data practices.

## Security

Please do not include passwords, license data, device identifiers, or other
private information in a public issue. Report security problems through GitHub's
private vulnerability reporting feature for this repository when it is
available. If it is unavailable, contact the repository maintainer privately
before sharing technical details publicly. Include the affected version and
steps to reproduce the issue; avoid attaching personal webcam footage.

Do not commit Firebase service-account files, private keys, `.env` files, or
other credentials. The Firebase client configuration included for the packaged
app is client-side configuration, not an administrator credential; server-side
access must be protected by Firebase security rules.

## License and third-party components

Unless a file says otherwise, VanishCam's original source code is available
under the [GNU General Public License v3.0](LICENSE) (GPL-3.0-only). You may
use, modify, and redistribute covered code under that license's terms. If you
redistribute a covered version, the GPL requires you to provide corresponding
source under GPL-3.0 and preserve the required notices. Read the complete
[`LICENSE`](LICENSE) before redistributing the project.

The GPL notice does not grant rights to third-party software, models, images,
character names, logos, or trademarks. Dependencies, MediaPipe models, and
assets may have separate terms; check their original sources and licenses
before redistributing them. OBS Virtual Camera is a separate project.
