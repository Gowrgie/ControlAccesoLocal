```mermaid
sequenceDiagram
    actor User
    participant App as Mobile Application
    participant API as Local HTTPS API
    participant Auth as Authentication Service
    participant DB as MySQL Database
    participant PIR as PIR Sensor
    participant Dispatcher as Access Dispatcher
    participant Controller as Raspberry Pi Controller
    participant Hardware as LEDs / Buzzer / Speaker / Motor
    %% USER LOGIN
    User->>App: Enter user ID and passcode
    App->>API: POST /sessions (credentials via HTTPS)
    API->>Auth: Validate login credentials
    Auth->>DB: Query user and password hash
    DB-->>Auth: Return user information
    Auth->>Auth: Verify passcode and user status
    Auth-->>API: Authentication result
    alt Valid credentials
        API-->>App: 200 OK (session token and expiration)
        App-->>User: Login successful
    else Invalid credentials
        API-->>App: 401 Unauthorized
        App-->>User: Display invalid credentials
    else Authentication service unavailable
        API-->>App: 503 Service Unavailable
        App-->>User: Display technical failure
    end
    %% AUTHENTICATED MOBILE SESSION
    opt Authenticated session
        %% PRESENCE VERIFICATION
        App->>API: GET /presence (Bearer token)
        API->>Auth: Validate active session
        API->>PIR: Read presence state
        PIR-->>API: Presence status
        alt Presence detected
            API-->>App: 200 OK (present = true)
            App-->>User: Enable access request
            %% ACCESS REQUEST
            User->>App: Request access
            App->>App: Generate unique request ID
            App->>API: POST /access-requests (request ID and Bearer token)
            API->>Auth: Validate session
            API->>PIR: Confirm active presence
            PIR-->>API: Current presence state
            alt Valid session and presence confirmed
                API->>Dispatcher: Check request ID
                Dispatcher-->>API: Existing or new request
                alt New request ID
                    API->>Dispatcher: Queue access request
                    Dispatcher-->>API: Pending or busy status
                    API-->>App: 202 Accepted (request ID and state)
                    %% ASYNCHRONOUS PROCESSING
                    par Raspberry Pi processes the request
                        Dispatcher->>Controller: Wait for available access operation
                        alt Request expires before execution
                            Dispatcher->>Dispatcher: Mark request as expired
                        else Controller becomes available
                            Controller->>PIR: Verify presence again
                            PIR-->>Controller: Presence status
                            alt Presence still valid
                                Controller->>Auth: Validate mobile user access
                                Auth->>DB: Query user, role, and permissions
                                DB-->>Auth: Return access data
                                Auth-->>Controller: Access validation result
                                alt Authorized
                                    Controller->>DB: Log authorized access
                                    Controller->>Hardware: Green LED and 3 short tones
                                    Controller->>Hardware: Play "Access granted"
                                    Controller->>Hardware: Activate motor
                                    Note over Controller,Hardware: Wait 3 seconds
                                    Controller->>Hardware: Return motor to resting position
                                else Without permission
                                    Controller->>DB: Log attempt without permission
                                    Controller->>Hardware: Red LED and 3 short tones
                                else Unrecognized user
                                    Controller->>DB: Log unrecognized attempt
                                    Controller->>Hardware: Red LED and 3 short tones
                                else System or database error
                                    Controller->>Hardware: Indicate failure with long tone
                                    Note over Controller,DB: Log failure only if database is available
                                end
                                Controller->>Controller: Clear operation and return to standby
                                Controller->>Dispatcher: Complete request with result
                            else Presence no longer valid
                                Controller->>Controller: Do not authorize opening
                                Controller->>Dispatcher: Complete request with system error
                            end
                        end
                    and Mobile application checks the result
                        loop Poll until complete or expired
                            App->>API: GET /access-requests/{request_id}
                            API->>Dispatcher: Query request status
                            Dispatcher-->>API: Current state and result
                            alt Pending or busy
                                API-->>App: 200 OK (pending or busy)
                                App-->>User: Display waiting status
                            else Complete
                                API-->>App: 200 OK (complete and result)
                                App-->>User: Display access result
                            else Expired
                                API-->>App: 200 OK (expired)
                                App-->>User: Display request timeout
                            end
                        end
                    end
                else Duplicate request ID
                    API-->>App: 409 Conflict (existing request status)
                    App-->>User: Display current request status
                end
            else Presence not detected
                API-->>App: 403 Forbidden
                App-->>User: Presence required
            else Invalid or expired session
                API-->>App: 401 Unauthorized
                App-->>User: Login required
            else Controller unavailable
                API-->>App: 503 Service Unavailable
                App-->>User: Display technical failure
            end
        else No presence detected
            API-->>App: 200 OK (present = false)
            App-->>User: Wait for presence detection
        else Presence service unavailable
            API-->>App: 503 Service Unavailable
            App-->>User: Display sensor error
        else Invalid or expired session
            API-->>App: 401 Unauthorized
            App-->>User: Login required
        end
        %% RETURN TO STANDBY
        App->>App: Clear current operation state
        App-->>User: Return to standby screen
    end
    