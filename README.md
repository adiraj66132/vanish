# VanishCam
<img width="1254" height="1254" alt="vanishcam_minimal_logo" src="https://github.com/user-attachments/assets/daa06215-cb7e-4ae5-97c3-77ad3b2458b5" />

VanishCam adds animated disappearance effects to a live webcam feed. Webcam
frames are processed on your computer and are not recorded or uploaded by this
app. Packaged builds also check licenses online; see [Privacy and network use](#privacy-and-network-use).

## Requirements

- Windows 10/11, Linux, or macOS (Intel or Apple silicon) and a working webcam
- Python 3.10 or newer
- Internet access the first time you install the Python packages
- Optional: OBS Studio with its Virtual Camera driver, for use in calls or streams
  (Windows); on Linux, the v4l2loopback kernel module for virtual camera output

Keep the camera still and use even lighting so your hands and body are easy to
see. The app needs a clear view of your room to create the background used by
the effects.

## Install and start

Open PowerShell in the project folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe vanish_cam.py
```

If `py` is not available, use `python` in its place. Choose an effect from the
menu, then select your webcam in the preview and press **Use this webcam** or
`Enter`. By default, VanishCam picks the highest common resolution supported by
the camera, while keeping the image's original proportions.

On Linux or macOS, run from a terminal in the project folder instead:

```bash
./run_local.sh
```

`run_local.sh` creates a Python virtual environment and installs dependencies on
first use, then starts the app. Source runs never perform an online license
check.

Before the effect starts, step completely out of view for about four seconds
while VanishCam captures the empty room. Return to the frame after the console
says the background is ready. Capture a new background with `Space` if the
camera or room has moved.

To start a particular effect without the menu, pass its mode name:

```powershell
.\.venv\Scripts\python.exe vanish_cam.py --mode normal
.\.venv\Scripts\python.exe vanish_cam.py --mode naruto
.\.venv\Scripts\python.exe vanish_cam.py --mode particles
.\.venv\Scripts\python.exe vanish_cam.py --mode goku
.\.venv\Scripts\python.exe vanish_cam.py --mode itachi
.\.venv\Scripts\python.exe vanish_cam.py --mode infinity
```

For example, to run Goku mode without virtual camera output:

```powershell
.\.venv\Scripts\python.exe vanish_cam.py --mode goku --no-virtual-camera
```

## Effects and gestures

- **Normal Vanish:** Raise your index and middle fingers in a V sign. Your
  silhouette dissolves. Press `R` to return.
- **Naruto Vanish:** Bring both palms together in front of you, fingers side by
  side rather than interlaced. Smoke and a falling log appear. Press `R` to
  return.
- **Particles:** Make the V sign. Your silhouette breaks into drifting colored
  fragments. Press `R` to return.
- **Goku:** Hold your straight, joined index and middle fingers against your
  forehead. The default hold time is one second; the app asks for a different
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

Click the preview window first so it receives keyboard input.

| Key | Action |
| --- | --- |
| `Space` | Capture the empty background again; leave the frame while it captures. |
| `R` | Return to the camera view (mode-specific gesture behavior applies). |
| `V` | Start the effect manually where supported. |
| `F` | Toggle fullscreen. |
| `Q` or `Esc` | Quit and release the camera. |

## Use with a virtual camera

VanishCam automatically tries to use OBS Virtual Camera when it is available.
In your call or streaming app, select **OBS Virtual Camera** as the camera.
Keep VanishCam running while using the effect.

To require virtual camera output, run:

```powershell
.\.venv\Scripts\python.exe vanish_cam.py --virtual-camera
```

To use the preview without virtual camera output, add `--no-virtual-camera`.
When using a Window Capture source in OBS, select the **Webcam Preview** window
and start OBS Virtual Camera from OBS. Only one app can provide OBS Virtual
Camera output at a time. Sound effects play through your computer's audio
output; virtual camera video does not include sound.

Virtual camera support by OS: on Windows, use OBS Virtual Camera or Unity
Capture (`--virtual-backend obs` or `--virtual-backend unitycapture`). On
Linux, load the v4l2loopback kernel module (`sudo modprobe v4l2loopback`) and
pass `--virtual-backend v4l2loopback`. macOS has no supported virtual camera
backend; start with `--no-virtual-camera` and capture the **Webcam Preview**
window with an OBS Window Capture source.

## Camera options

Choose a specific camera by index, or set a resolution and virtual output frame
rate. Specify both width and height together. For example:

```powershell
.\.venv\Scripts\python.exe vanish_cam.py --camera 1 --width 1280 --height 720 --fps 30
```

The preview preserves the camera's aspect ratio instead of stretching the image.
For gesture troubleshooting, add `--gesture-debug`; diagnostics appear in the
terminal, not over the video.

## Launchers and build

Windows: `RUN_LOCAL.bat` starts the local Python version. `RUN_VIRTUAL.bat`
requires virtual camera output, and `RUN_OBS.bat` starts without direct virtual
camera output for an OBS Window Capture setup. You can pass the same options
after the batch file, for example:

```powershell
.\RUN_LOCAL.bat --mode infinity
```

Linux/macOS: `./run_local.sh` starts the app, `./run_virtual.sh` requires
virtual camera output, and `./run_obs.sh` starts without direct virtual camera
output. Pass the same options after the script name, for example:

```bash
./run_local.sh --mode infinity
```

To build the Windows executables, install Python and run `BUILD_WINDOWS.bat`.
On Linux/macOS, run `./build_unix.sh`. Both create a build environment, check
the MediaPipe models, and self-test the packaged apps. The generated files are
placed in `dist\` (Windows) or `dist/` (Linux/macOS). Packaged builds on Linux
and macOS skip license checks; only Windows editions activate a license.

## Troubleshooting

- **Camera not found:** Close other apps using the webcam, check your operating
  system's camera permissions, and try another camera in the selection screen.
- **Effect does not trigger:** Improve the lighting, keep your full hand in the
  frame, and perform the gesture clearly.
- **Background looks wrong:** Press `Space`, leave the frame for the full
  capture, and keep the camera still.
- **Virtual camera unavailable:** On Windows, install the OBS Virtual Camera
  driver and make sure another app is not already using its output. On Linux,
  load `v4l2loopback`. On macOS, virtual camera output is not supported; use an
  OBS Window Capture source instead.
- **Video is slow:** Try a smaller resolution, such as `--width 640 --height 360`.
- **No sound:** If pygame's mixer module is unavailable (some Python 3.14
  builds ship without it), VanishCam falls back to `ffplay`; install ffmpeg
  (which provides ffplay), or use Python 3.13 or older for built-in playback.

## Privacy and network use

The effects process the live camera feed locally. VanishCam does not send
webcam frames or captured backgrounds to its license service. The Python source
run directly with Python does not require an online license check. Packaged
Windows editions use Firebase for license activation and session checks; these
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
