# VanishCam License Administration

Firebase project: **vanishcam-licenses-20261027** (VanishCam Licenses).

[Open Firestore](https://console.firebase.google.com/project/vanishcam-licenses-20261027/firestore/databases/-default-/data).
The database is `(default)`, in location `nam5`. Cloud Functions, a private
server, and administrative credentials inside the EXEs are not required. The
project uses the free plan; Firebase quotas still apply. This code does not link
a billing account or enable the Identity Platform upgrade.

## Activate a license

1. Open Firestore Database > Data.
2. Create the `licenses` collection if it does not exist.
3. Create a document whose ID is the customer's email address in lowercase,
   with no spaces. Example: `customer@example.com`.
4. Add an `email` field of type **string** with the same address.
5. Add an `active` field of type **boolean** with value **true**. Do not use the
   string `"true"`; it must be a boolean value.
6. Save. The customer can open any edition and enter that email address.

You do not need to create an email/password user in Firebase Authentication.
The app automatically generates an anonymous identity for the device. Customers
do not register, create a password, or receive an email confirmation.

## Deactivate or reactivate a license

In the `licenses/EMAIL` document, change `active` to **false**. New launches are
rejected immediately. An app that is already open stops at its next check,
usually within about 25 seconds plus network time. To reactivate, set it to
**true** again. After revocation or a forced close without releasing the
session, you may need to wait for the old session to expire, at most two minutes
after its last renewal.

## Move a license to another PC or reset a reinstalled Windows profile

1. Set `licenses/EMAIL.active = false`.
2. Ask the customer to close the app and wait two minutes so no valid session remains.
3. In the Firestore console, delete ONLY the `licenseBindings/EMAIL` document.
   Do not delete the license or remove active sessions to force an unlock; the
   expiry protects against simultaneous use during the transfer.
4. Set `licenses/EMAIL.active = true` again.
5. The customer enters the same email on the new PC. The first successful
   activation creates the new device binding. The old device will be rejected.

This reset is also needed after protected local data is removed or Windows is
reinstalled: the previous anonymous identity cannot be recovered from the email
address alone. Do not delete anonymous users in Authentication if you want to
keep their existing bindings.

## Automatically created data

| Collection | Contents | Management |
| --- | --- | --- |
| `licenses/EMAIL` | Email and `active` status | Manage this in the console |
| `licenseBindings/EMAIL` | Anonymous UID, device hash, binding date | App managed; delete only for an authorized transfer |
| `licenseSessions/EMAIL` | UID, device hash, session ID, mode, `lastSeenAt`, `released` | App managed; normally do not edit |

The mode is informational: all editions share one license; customers do not buy
a separate license for each effect. Only one app instance may be active at a
time, even if two EXEs are on the same PC. Effects added before the rules were
updated, such as Itachi, are temporarily reported as `full`. The license keeps
renewing without expanding the device or session permissions.

## How the limit is enforced

- The PC receives an anonymous Firebase identity; the customer does not enter
  credentials.
- The refresh token and email are stored with Windows DPAPI in the current
  profile under `%LOCALAPPDATA%\VanishCam\licensing\PROJECT_ID\identity.bin`.
- The device is identified by a hash of the Windows MachineGuid. The original
  GUID is not sent to Firebase. DPAPI credentials copied to another PC or
  Windows profile normally cannot be decrypted there.
- Activation uses an atomic Firestore write with version preconditions. Server
  rules check the active license, device binding and exclusive session; changing
  a local value alone is not enough.
- The app renews the session every 25 seconds using the server timestamp. A
  session expires after 120 seconds without renewal. Normal shutdown releases
  it immediately; after a crash it expires automatically.
- If the network is unavailable, the app does not extend validity on its own.
  It stops output before server expiry, with a 15-second margin. Every launch
  requires a successful online check, even when the email is already saved.
- Checks continue in menus and previews, and before every virtual frame is sent.
  Revocation also closes the webcam, virtual output and audio.

An email address alone does not prove that the person entering it owns the
mailbox. As requested, the app does not require passwords or confirmation. A
person who knows an active email can attempt the first binding while it is not
yet assigned to a PC. After binding, the protected device identity and a valid
session are also required. For this reason, activate the email when delivering
the product to the customer. Like any license checked by a local program, this
is basic commercial protection, not inviolable DRM.

## Distribution and maintenance

`license_config.json` contains public Firebase configuration and must be
included in every build. `VanishCam.spec` includes it automatically in all
editions. PyInstaller includes `license_client.py` through its import. Do not
distribute service credentials, CLI logins, your Windows profile data, or the
`licensing_backend/node_modules` development folder.

Rebuild with `BUILD_WINDOWS.bat` and distribute the new EXEs. Older copies
without license checks do not gain this feature retroactively. `--self-test`
checks models and files only, without a webcam or effects, and does not require
a license. Distributed EXEs do not have an offline mode. Python scripts started
by `RUN_LOCAL.bat` are the local development version and run without Firebase
license checks.

Private rules are in `licensing_backend/firestore.rules`, which is excluded
from Git. Make sure this file exists in your local copy before running tests or
publishing changes. To deploy rules:

```powershell
cd licensing_backend
$env:DEBUG = ''
firebase deploy --only firestore:rules --project vanishcam-licenses-20261027
```

To test the rules (Node 22+, Java and Firebase CLI):

```powershell
npm ci
$env:DEBUG = ''
firebase emulators:exec --only firestore --project demo-vanishcam-licenses "npm test"
```

Tests use an emulated demo project, not customer licenses. The desktop client
does not need administrative Firebase credentials.

## Privacy

The product privacy notice should describe the data sent to Firebase: email,
anonymous identifier, hashed device identifier, and session status, including
timestamps and mode. Network services may process technical request metadata.
These checks do not send webcam images or audio. Any previous statement that
"everything is offline" does not apply to license checks.

References: [anonymous identities](https://firebase.google.com/docs/auth/web/anonymous-auth),
[Firestore rules](https://firebase.google.com/docs/firestore/security/rules-conditions),
[REST API](https://firebase.google.com/docs/firestore/use-rest-api).
