# VanishCam User Guide

Guide for the VanishCam desktop app on Windows and Linux.

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
open at a time.** Close it before opening another copy.
To move your license to a different PC, contact support for a device reset.
Copying the EXE does not transfer the license. Do not delete the local license
data or reinstall Windows as a way to fix an activation error: a device reset
may then be needed.

After a crash or forced shutdown, wait up to **two minutes** before trying
again. If the license is disabled or Internet access is lost for too long,
the app stops and releases the cameras. Reconnect or contact support, then
reopen the app.

### 4. Choose your effect

The single VanishCam app contains all effects. In the launcher window, click
one of the effect cards: Normal Vanish, Naruto Vanish, Particles, Goku, Itachi
Uchiha or Infinity Gauntlet. Your last choice is remembered for next time.

### 5. Select the webcam and capture the background

1. In the launcher, check the live camera thumbnail.
2. Change **Webcam index** until the right camera appears. You can also choose
   a fixed **Resolution** (Auto picks the highest common mode), the virtual
   camera FPS, mirror setting, and virtual camera backend.
3. Click **Start effect**.
4. **Step completely out of the camera frame for four seconds.** The app
   captures the empty room. Keep your hands out of view too.
5. Wait for the status message saying the background is ready, then step
   back into the frame. You can now perform the gesture for your effect.

The preview preserves the camera's aspect ratio, so the image does not stretch.
Settings are saved when you start the effect and reused on the next launch.

Capture the background again with `Space` whenever you move the webcam or
change the scene. People or objects moving behind you can affect the result.

### 6. Activate an effect and reappear

| Effect | How to activate it | How to reappear |
| --- | --- | --- |
| **Normal Vanish** | Raise your index and middle fingers in a V sign. Your silhouette dissolves over about 3.6 seconds. | Press `R`. |
| **Particles** | Make the same V sign. Your silhouette breaks into drifting fragments over about 2.1 seconds. | Press `R`. |
| **Naruto Vanish** | Bring both palms together, with fingers side by side, not interlaced. Keep both hands visible. Smoke and a falling wooden log replace you. | Press `R`. |
| **Goku** | Hold your straight, joined index and middle fingers against your forehead for three seconds. Comic-style streaks accompany the teleport. | Lower your hand and repeat the gesture for three seconds, or click **Reappear**. |
| **Itachi Uchiha Disappear** | Touch both hands together in front of the center of your chest. Your silhouette turns into flapping crows over about 4 seconds; a translucent blood-red texture covers the room and Sharingan eyes briefly appear at the top. The red background remains while you are invisible. | Release your hands, return to the frame, then touch them at your chest again. The crows rebuild your silhouette and the room returns to normal. |
| **Infinity Gauntlet** | Show one hand. The drawn gauntlet follows your hand. Touch your thumb and middle fingertip, then snap them apart with a quick movement. After a 3-second delay, your silhouette dissolves into cosmic dust. | Press `R` to return to the camera view. |

For Goku, release the pose before using it again. If the pose is interrupted,
you may need to start the hold again. The effect window shows the countdown.
Sound plays on both disappearance and reappearance; Naruto plays sound when you
disappear. Normal Vanish and Particles do not add a sound effect.

### 7. Keyboard controls

Use the buttons at the bottom of the effect window, or the shortcuts below
while that window has focus.

| Key | Action |
| --- | --- |
| `Space` | Capture a new background. Step out of view for four seconds again. |
| `R` | Reappear in every mode. In Goku it starts the animated return; repeat the gesture if you prefer. |
| `V` | Manually start Normal, Naruto, Particles or Itachi. Disabled in Goku and Infinity Gauntlet modes (their **Vanish** button is disabled too). |
| `F` | Toggle fullscreen. |
| `Q` or `Esc` | Exit the app and release the cameras and license session. |

To change effects, quit the effect window (`Q`) and pick another card in the
launcher. Closing the effect window returns you to the launcher.

### 8. Use the effect in a video call

1. Install OBS Studio with the OBS Virtual Camera driver.
2. If OBS is open, make sure its **Start Virtual Camera** output is stopped.
3. Open VanishCam, activate your license, select the webcam and capture the
   background. Leave **Virtual camera** on **auto**, or set it to **on**.
4. Check the status line for confirmation that virtual output is active.
5. In your video-call or streaming app, choose **OBS Virtual Camera** as
   the camera instead of your physical webcam. Keep VanishCam running.

The preview and virtual output show the same video. The virtual camera carries
video, not the sound effects. Sounds play through your computer's audio output;
to send them to a call or stream, configure that app to capture computer audio.

If you instead want to compose a scene inside OBS, set **Virtual camera** to
**off** in the launcher before starting the effect. In OBS add a **Window
Capture** source for the **Webcam Preview** window, then start the virtual
camera from OBS. Choose either direct output from VanishCam or output from OBS;
both cannot produce OBS Virtual Camera at the same time.

### 9. Troubleshooting

| Problem | What to do |
| --- | --- |
| License not active | Check the spelling of your license email and ask the seller/support team to verify activation. |
| License associated with another PC | Ask support to transfer/reset the device association. |
| Another copy is already running | Only one instance can use the camera and license. Close it before starting again. After a crash, wait up to two minutes. |
| License check or connection error | Check Internet access, wait a moment and reopen the app. Internet is required during use. |
| Webcam unavailable | Close other apps using the physical webcam, check Windows camera permissions and try another camera index in the launcher. |
| Background looks wrong or you remain visible | Press `Space`, leave the frame completely for four seconds, then return. Keep the webcam still. |
| Gesture not recognized | Improve lighting, keep the hand fully in view and hold the correct pose clearly. For Goku, keep two joined fingers at your forehead for a full second. |
| Keyboard shortcuts do nothing | Click the effect window first. `V` is disabled in Goku and Infinity Gauntlet; their **Vanish** button is greyed out. `R` works in every mode. |
| Virtual camera unavailable | Check that the driver is installed and OBS is not already producing virtual output. You can use the local preview without a virtual camera. |
| No sound | Check the Windows volume mixer, selected output and speakers/headphones. Normal and Particles are silent. |
| Video is slow | Close demanding apps, then choose a smaller resolution in the launcher (for example 640 x 360) and lower the virtual camera FPS. |

If a problem persists, send support your Windows version and the error text
shown in the dialog or in the log file under
`%LOCALAPPDATA%\VanishCam\logs\vanishcam.log`. Never send local license
credential files.

### 10. Privacy

Webcam frames are processed on your PC. VanishCam does not record or upload
your webcam feed. Empty-background images are used in memory for the effect.
License checks send your license email, an anonymous installation identifier,
a hashed device identifier and session information to Firebase. No password
is collected. Video-call or streaming software you use has its own data practices.

---
