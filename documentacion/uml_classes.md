```mermaid
classDiagram
    direction LR
    %% MAIN APPLICATION
    class MainActivity {
        +onCreate()
    }
    class AppNavigation {
        <<composable>>
        +AppNavigation()
    }
    %% USER INTERFACE
    class IdentificationScreen {
        <<composable>>
        +IdentificationScreen(onLoggedIn)
    }
    class RequestScreen {
        <<composable>>
        +RequestScreen(presenceDetected, onRequestAccess)
    }
    class ResultScreen {
        <<composable>>
        +ResultScreen(result, onReturnToStandby)
    }
    %% API COMMUNICATION
    class ApiClient {
        <<singleton>>
        +service: ApiService
    }
    class ApiService {
        <<interface>>
        +login(request: LoginRequest) SessionResponse
        +createBiometricChallenge(request: BiometricChallengeRequest) BiometricChallenge
        +loginBiometrically(request: BiometricSessionRequest) SessionResponse
        +logout(token: String) void
        +getPresence(token: String) PresenceResponse
        +createAccessRequest(token: String, request: AccessRequestCreate) AccessRequestStatus
        +getAccessRequestStatus(token: String, requestId: String) AccessRequestStatus
    }
    class DeviceBiometrics {
        +disponible(context)
        +vinculada()
        +crearClave()
        +guardar(id, alias)
        +firmar(activity, alias, reto)
    }
    class AndroidKeystore
    class BiometricPrompt
    %% AUTHENTICATION MODELS
    class LoginRequest {
        +identificador: String
        +clave: String
        +biometricPublicKey: String?
    }
    class SessionResponse {
        +token: String
        +expira: String
        +biometricCredentialId: String?
    }
    %% PRESENCE MODEL
    class PresenceResponse {
        +present: Boolean
    }
    %% ACCESS REQUEST MODELS
    class AccessRequestCreate {
        +requestId: String
    }
    class AccessRequestStatus {
        +requestId: String
        +state: String
        +result: String
    }
    %% ERROR MODEL
    class ErrorResponse {
        +error: String
    }
    %% APPLICATION RELATIONSHIPS
    MainActivity --> AppNavigation : hosts
    AppNavigation --> IdentificationScreen : identification
    AppNavigation --> RequestScreen : access request
    AppNavigation --> ResultScreen : access result
    %% SCREEN DEPENDENCIES
    IdentificationScreen ..> ApiClient : sign-in
    IdentificationScreen --> DeviceBiometrics : link and authenticate
    DeviceBiometrics ..> AndroidKeystore : store and use key
    DeviceBiometrics ..> BiometricPrompt : authorize signing
    AppNavigation ..> ApiClient : presence, access request, status, logout
    %% API RELATIONSHIPS
    ApiClient "1" --> "1" ApiService : provides
    ApiService ..> LoginRequest : sends
    ApiService ..> SessionResponse : receives
    ApiService ..> PresenceResponse : receives
    ApiService ..> AccessRequestCreate : submits
    ApiService ..> AccessRequestStatus : receives
    ApiService ..> ErrorResponse : handles
    %% DATA RELATIONSHIPS
    SessionResponse "1" --> "0..*" AccessRequestCreate : authorizes
    AccessRequestCreate "1" --> "0..*" AccessRequestStatus : status updates
    ```
