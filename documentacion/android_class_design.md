# Android Application Class Design

The app identifies the user, checks PIR presence, sends an access request, and displays the result from the Raspberry Pi. The Raspberry Pi verifies credentials and sessions, checks presence when it receives a new request, validates user permissions, and controls the door. Android uses the presence status to enable the **Request access** button and displays the server’s decision.

## Layers and Responsibilities

| Layer | Current Implementation | Proposed Design |
| --- | --- | --- |
| UI | `IdentificationScreen` offers ID and passcode sign-in, device linking, and Android biometric sign-in. `RequestScreen` displays presence. `ResultScreen` displays the request status and result. `AppNavigation` coordinates navigation and handles most API calls. | The screens receive UI state and emit events. `AccesoViewModel` manages the session, periodic status checks, the request UUID, and the state shown on each screen. |
| Domain | The app keeps the session token in memory. Navigation manages the request UUID, status, and result. | `UsuarioIdentificado`, `SesionMovil`, and `SolicitudAcceso` model the access flow. `EstadoSolicitud`, `ResultadoAcceso`, and `EstadoPresencia` represent its states and outcomes. |
| Repository and client | `ApiClient` configures Retrofit, OkHttp, and Gson. `ApiService` declares the HTTP operations. `DeviceBiometrics` manages the linked credential and requests Android Keystore signatures through the system biometric prompt. | `RepositorioAcceso` defines the operations used by the UI. `RepositorioAccesoRemoto` calls `ApiService` and maps transport models, HTTP responses, and network failures to values the app can handle. |

## Entities and Relationships

- **`UsuarioIdentificado`.** Represents the account resolved by the Raspberry Pi from the sign-in method. A passcode sign-in starts with the identifier from the form. A biometric sign-in resolves the account from the linked public key. The server returns a session token and expiration. It looks up roles and permissions when handling an access request.
- **`SesionMovil`.** The proposed model holds the token and expiration in memory during the access flow. The current navigation keeps the token. Each protected request includes `Authorization: Bearer <token>`. The app uses the password to sign in and clears it after a successful sign-in.
- **Device credential.** Phone linking stores an opaque credential ID and a Keystore alias in the app. The Raspberry Pi stores the public key and the linked user ID. Both sign-in paths produce the same session model.
- **`SolicitudAcceso`.** Holds the UUID generated for a new request, the status reported by the server, and the result when available. A session can have multiple requests over its lifetime, and the UI tracks one at a time. If the app cannot confirm whether a submission succeeded, it keeps the same UUID to check its status.
- **`EstadoPresencia`.** Represents active, inactive, or unknown presence. The **Request access** button is enabled only when presence is active. The UI gets this state from the `present` field before submitting a request.
- **`EstadoSolicitud` and `ResultadoAcceso`.** A request can be `pending`, `busy`, `complete`, or `expired`. When the request reaches `complete`, the server can return `autorizado`, `sin_permiso`, `no_reconocido`, or `error_sistema`. The UI displays a technical error or a pending confirmation when communication fails. A `sin_permiso` result displays an access denial.

## Proposed Class Diagram

[Proposed Android class diagram](../diagramas/android_proposed_class_diagram.md)

`SolicitudAcceso.resultado` is optional until the server publishes a result. In the proposed design, the Compose screen functions consume the state exposed by `AccesoViewModel`.

## API Communication and Result Handling

| Operation | Endpoint | Response Handling |
| --- | --- | --- |
| Sign in | `POST /sessions` | `200` starts the flow with the token and expiration time. A `401` during sign-in displays an invalid credentials message, a `429` displays a too-many-attempts message, and a `503` indicates the authentication service is unavailable. |
| Link a phone | `POST /sessions` with `biometric_public_key` | A successful password sign-in returns `biometric_credential_id`. |
| Sign in with biometrics | `POST /sessions/biometric/challenge`, then `POST /sessions/biometric` | The app obtains a challenge, asks Android to authorize signing, and submits the signature for the standard session response. |
| Update the request button | `GET /presence` | `200` updates the presence status. If the check fails, the app disables the request button while the status is unknown. |
| Submit an access request | `POST /access-requests` | `202` confirms acceptance for processing. `409` for a UUID owned by the current session indicates that the request already exists and its status can be checked. `403` can indicate that presence is inactive or that the UUID belongs to another session. |
| Check the result | `GET /access-requests/{request_id}` | `200` updates the request status. The UI displays the result when the status reaches `complete` and shows an expiration message when it reaches `expired`. |
| Return to sign-in | `DELETE /sessions` | Android clears the local state and requests session closure. `204` confirms that the session was revoked or had already ended. |

The app connects to `raspberrypi.local:8000` over HTTPS using the project’s certificate authority. A `401` from a protected endpoint prompts the user to sign in again. In the proposed design, the repository exposes the wait time from `Retry-After` when it receives a `429` so the app can schedule the next check. If a network failure leaves the outcome of a request uncertain, Android can check its status again using the original session and UUID.

The current app checks for a result for up to 20 seconds. If that period ends without confirmation, the UI indicates that the result is still unknown. The app shows an expiration message when the server reports `expired`. After displaying a definitive result, the app can return to sign-in automatically after 6 seconds.
