# VanishCam User Guide

Guide for the Windows EXE editions.

### 1. What VanishCam does

VanishCam adds disappearance effects to your webcam video. Choose an effect,
capture the empty background, then perform the matching hand gesture. You can
watch the result in the preview or use it in video calls and streams through
a virtual camera.

### 2. What you need

- A 64-bit Windows PC, a working webcam and an active Internet connection.
- An active license for the email address supplied with your purchase.
- Speakers or headphones for the Naruto and Goku sound effects.
- Optional: OBS Studio with its OBS Virtual Camera driver for video calls.

You do not need to install Python. If the download is a ZIP archive, extract
it before opening the EXE. Keep your camera still and use even lighting so
your face and hands are clearly visible.

### 3. Activate your license

1. Open the EXE you received. Allow a few moments for startup.
2. On first launch, enter the email associated with your license.
3. Click **Activate and Start**.
4. Once the license is accepted, continue to the effect/camera selection.

**Only your email is required.** There is no password, registration form or
email confirmation. If your email has not yet been activated, contact the
seller or support team that provided your license.

The app remembers your email in your Windows profile. On later launches it
still checks the license online before starting, then checks it periodically
while you use the app. There is no offline activation mode.

Your license is associated with one PC. **Only one VanishCam instance may be
open at a time, across all editions.** Close one edition before opening another.
To move your license to a different PC, contact support for a device reset.
Copying the EXE does not transfer the license. Do not delete the local license
data or reinstall Windows as a way to fix an activation error: a device reset
may then be needed.

After a crash or forced shutdown, wait up to **two minutes** before trying
again. If the license is disabled or Internet access is lost for too long,
the app stops and releases the cameras. Reconnect or contact support, then
reopen the app.

### 4. Choose your effect

| EXE | Available effects |
| --- | --- |
| `VanishCam.exe` | Normal Vanish (`1`), Naruto Vanish (`2`), Particles (`3`), Goku (`4`), Itachi (`5`), Infinity Gauntlet (`6`) |
| `Naruto Vanish Effect.exe` | Naruto, selected automatically |
| `Goku Vanish Effect.exe` | Goku, selected automatically |
| `Normal and Particles Vanish.exe` | Normal Vanish (`1`) or Particles (`2`) |

Where a menu is shown, click an effect or press its number.

### 5. Select the webcam and capture the background

1. In the webcam selection screen, check the live preview.
2. Use the `-` / `+` buttons, keys `0`–`9`, or `A` / `D` to change cameras.
3. Click **USE THIS WEBCAM** or press `Enter` to confirm.
   Press `R` to retry the selected camera, or `Esc` to cancel.
4. **Step completely out of the camera frame for four seconds.** The app
   captures the empty room. Keep your hands out of view too.
5. Wait for the console message saying the background is ready, then step
   back into the frame. You can now perform the gesture for your effect.

By default, VanishCam tries common camera modes from highest to lowest and
uses the highest common resolution the webcam accepts. The preview preserves the
camera's aspect ratio, so the image does not stretch to fill the preview box.
To choose a resolution manually, pass both `--width` and `--height` when
starting the app.

Capture the background again with `Space` whenever you move the webcam or
change the scene. People or objects moving behind you can affect the result.
You can minimize the console window; closing it may also close the app.

### 6. Activate an effect and reappear

| Effect | How to activate it | How to reappear |
| --- | --- | --- |
| **Normal Vanish** | Raise your index and middle fingers in a V sign. Your silhouette dissolves over about 3.6 seconds. | Press `R`. |
| **Particles** | Make the same V sign. Your silhouette breaks into drifting fragments over about 2.1 seconds. | Press `R`. |
| **Naruto Vanish** | Bring both palms together, with fingers side by side, not interlaced. Keep both hands visible. Smoke and a falling wooden log replace you. | Press `R`. |
| **Goku** | Hold your straight, joined index and middle fingers against your forehead for one second. Comic-style streaks accompany the teleport. | Lower your hand, then repeat the gesture for one second. |
| **Itachi Uchiha Disappear** | Touch both hands together in front of the center of your chest. Your silhouette turns into flapping crows over about 4 seconds; a translucent blood-red texture covers the room and Sharingan eyes briefly appear at the top. The red background remains while you are invisible. | Release your hands, return to the frame, then touch them at your chest again. The crows rebuild your silhouette and the room returns to normal. |
| **Infinity Gauntlet** | Show one hand. The drawn gauntlet follows your hand. Touch your thumb and middle fingertip, then snap them apart with a quick movement. After a 3-second delay, your silhouette dissolves into cosmic dust. | Press `R` to return to the camera view. |

For Goku, release the pose before using it again. If the pose is interrupted,
you may need to start the hold again. The console shows the countdown. Sound
plays on both disappearance and reappearance; Naruto plays sound when you
disappear. Normal Vanish and Particles do not add a sound effect.

### 7. Keyboard controls

Click the preview window first so it receives your keyboard input.

| Key | Action |
| --- | --- |
| `Space` | Capture a new background. Step out of view for four seconds again. |
| `R` | Reappear in Normal, Naruto, Particles or Infinity Gauntlet; start the animated return in Itachi after you return to frame. Disabled in Goku mode. |
| `V` | Manually start Normal, Naruto, Particles or Itachi. Disabled in Goku and Infinity Gauntlet modes. |
| `F` | Toggle fullscreen. |
| `Q` or `Esc` | Exit the app and release the cameras and license session. |

To change effects after starting the webcam, exit and reopen the app.

### 8. Use the effect in a video call

1. Install OBS Studio with the OBS Virtual Camera driver.
2. If OBS is open, make sure its **Start Virtual Camera** output is stopped.
3. Open VanishCam, activate your license, select the webcam and capture the
   background. VanishCam automatically tries to open OBS Virtual Camera.
4. Check the console for confirmation that virtual output is active.
5. In your video-call or streaming app, choose **OBS Virtual Camera** as
   the camera instead of your physical webcam. Keep VanishCam running.

The preview and virtual output show the same video. The virtual camera carries
video, not the sound effects. Sounds play through your computer's audio output;
to send them to a call or stream, configure that app to capture computer audio.

If you instead want to compose a scene inside OBS, launch VanishCam without
direct virtual output. Open PowerShell in the EXE folder and run, for example:

```powershell
& ".\VanishCam.exe" --no-virtual-camera
```

In OBS add a **Window Capture** source for **Webcam Preview**, then start
the virtual camera from OBS. Choose either direct output from VanishCam or
output from OBS; both cannot produce OBS Virtual Camera at the same time.

### 9. Troubleshooting

| Problem | What to do |
| --- | --- |
| License not active | Check the spelling of your license email and ask the seller/support team to verify activation. |
| License associated with another PC | Ask support to transfer/reset the device association. |
| Another edition is already open | Close it before starting this one. After a crash, wait up to two minutes. |
| License check or connection error | Check Internet access, wait a moment and reopen the app. Internet is required during use. |
| Webcam unavailable | Close other apps using the physical webcam, check Windows camera permissions and try another camera in the selection screen. |
| Background looks wrong or you remain visible | Press `Space`, leave the frame completely for four seconds, then return. Keep the webcam still. |
| Gesture not recognized | Improve lighting, keep the hand fully in view and hold the correct pose clearly. For Goku, keep two joined fingers at your forehead for a full second. |
| Keyboard shortcuts do nothing | Click the preview window first. Remember that `R` and `V` are disabled in Goku; `V` is also disabled in Infinity Gauntlet. |
| Virtual camera unavailable | Check that the driver is installed and OBS is not already producing virtual output. You can use the local preview without a virtual camera. |
| No sound | Check the Windows volume mixer, selected output and speakers/headphones. Normal and Particles are silent. |
| Video is slow | Close demanding apps. For a lower workload, run the command below from PowerShell in the EXE folder. |

```powershell
& ".\VanishCam.exe" --width 640 --height 360 --fps 24
```

Replace `VanishCam.exe` with the filename of your edition when needed. If a
problem persists, send support the EXE name, your Windows version and the
error text shown in the console. Never send local license credential files.

### 10. Privacy

Webcam frames are processed on your PC. VanishCam does not record or upload
your webcam feed. Empty-background images are used in memory for the effect.
License checks send your license email, an anonymous installation identifier,
a hashed device identifier and session information to Firebase. No password
is collected. Video-call or streaming software you use has its own data practices.

---
