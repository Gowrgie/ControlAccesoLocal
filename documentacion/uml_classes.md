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
        +logout(token: String) void
        +getPresence(token: String) PresenceResponse
        +createAccessRequest(token: String, request: AccessRequestCreate) AccessRequestStatus
        +getAccessRequestStatus(token: String, requestId: String) AccessRequestStatus
    }
    %% AUTHENTICATION MODELS
    class LoginRequest {
        +identificador: String
        +clave: String
    }
    class SessionResponse {
        +token: String
        +expira: String
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
    IdentificationScreen ..> ApiClient : login
    RequestScreen ..> ApiClient : presence and access
    AppNavigation ..> ApiClient : session and status
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