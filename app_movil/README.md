# AppMovil

Android app for ControlAccesoLocal. It is a fourth access method: a user identifies, requests access, and sees the result — using the same validation logic as the other methods, through the Raspberry Pi's API.

## Requirements

- Android Studio (includes JDK, SDK, and emulator)
- Minimum SDK: API 24

## How to run

1. Open `app_movil/` in Android Studio.
2. Wait for Gradle sync.
3. Build → Assemble Project with Tests.
4. Run on an emulator or a connected device.

## Structure

```
ui/        # the three screens (identification, request, result)
domain/    # models: user, session, result
data/      # HTTP client
navigation/
```

## System status

In development.