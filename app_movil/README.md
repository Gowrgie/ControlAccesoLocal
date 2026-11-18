# AppMovil

Android client for ControlAccesoLocal. After signing in, the user can request
access when the Raspberry Pi reports PIR presence. The Raspberry Pi checks
permissions and returns the access result.

## Build and run

- Android Studio with the Android SDK used by `app/build.gradle.kts`.
- Minimum runtime SDK is Android 7.0 (API 24).
- The Raspberry Pi must run the HTTPS API on the same local network. See the
  [mobile API contract](../documentacion/mobile_api_contract.md) for setup.

To install a debug build on a connected Android device from this directory:

```bash
bash ./gradlew :app:installDebug
```

## Sign in

1. To use a passcode, enter the project user ID and passcode.
2. To link a compatible phone, configure a Class 3 biometric in Android
   settings. On a password sign-in, select **Activar biometría en este
   teléfono**. The Raspberry Pi must have the biometric credential migration.
3. Return to identification and select **Ingresar con biometría**. Follow the
   Android prompt. A successful sign-in opens **Solicitud de acceso**.
   Android may provide a fingerprint or face, depending on the device.

The Moto e13 was tested with ID and passcode. Android reported no Class 3
biometric available to the app on that test device. Biometric sign-in on a
compatible handset remains to be tested.

## Source layout

| Package | Responsibility |
| --- | --- |
| `ui/` | Identification, access request, and result screens |
| `navigation/` | Navigation, session state, presence checks, and access request status |
| `data/` | HTTP service, transport models, and the Android Keystore biometric credential |

- [Android class design](../documentacion/android_class_design.md)
- [Original mobile wireframes](../wireframe/app). The identification mockups show the earlier passcode layout. The current identification screen adds phone linking and invokes the Android system prompt for biometric sign-in.
