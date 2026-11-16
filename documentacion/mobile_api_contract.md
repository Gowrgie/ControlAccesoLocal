Mobile API Contract
The Raspberry Pi exposes a local HTTPS service for the Android app. It reuses
the existing validation logic (access_logic.py) and authentication module
(autenticacion.py). The service is reachable only from the local network
(NFR-14).
Security
All endpoints use HTTPS with TLS 1.2 or later. Protected operations use
Authorization: Bearer <token>. See [Mobile API security](mobile_security.md)
for certificate trust, session handling, and rate limits.
OpenAPI contract
openapi: 3.0.3
info:
  title: ControlAccesoLocal Mobile API
  version: "1.0"
  description: >
    Local HTTPS service for the Android app. The controller owns the hardware
    and processes access requests through its dispatcher.

servers:
  - url: https://raspberrypi.local:8000

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

  schemas:
    LoginRequest:
      type: object
      required: [identificador, clave]
      properties:
        identificador:
          type: string
        clave:
          type: string
          format: password
          writeOnly: true

    Session:
      type: object
      required: [token, expira]
      properties:
        token:
          type: string
        expira:
          type: string
          format: date-time

    Presence:
      type: object
      required: [present]
      properties:
        present:
          type: boolean

    AccessRequestCreate:
      type: object
      required: [request_id]
      properties:
        request_id:
          type: string
          format: uuid
          description: >
            Client-generated idempotency key. The controller retains request IDs
            in memory for the lifetime of the process.

    AccessRequestStatus:
      type: object
      required: [request_id, state, result]
      properties:
        request_id:
          type: string
          format: uuid
        state:
          type: string
          enum: [pending, busy, complete, expired]
        result:
          type: string
          enum: [autorizado, sin_permiso, no_reconocido, error_sistema, null]
          nullable: true

    Error:
      type: object
      required: [error]
      properties:
        error:
          type: string

  responses:
    UnauthorizedSession:
      description: Session token is missing, invalid, or expired
      headers:
        WWW-Authenticate:
          schema:
            type: string
            example: Bearer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    InvalidRequest:
      description: Invalid request data
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    TooManyRequests:
      description: The request limit has been reached
      headers:
        Retry-After:
          description: Seconds to wait before retrying
          schema:
            type: integer
            minimum: 1
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    AuthenticationUnavailable:
      description: Authentication service is unavailable
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

paths:
  /sessions:
    post:
      summary: Log in and start a session
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Session created, with the expiration timestamp in UTC
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          $ref: '#/components/responses/InvalidRequest'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '503':
          $ref: '#/components/responses/AuthenticationUnavailable'
    delete:
      summary: Log out
      security:
        - bearerAuth: []
      responses:
        '204':
          description: Session closed or already absent
        '401':
          description: A Bearer token is required
          headers:
            WWW-Authenticate:
              schema:
                type: string
                example: Bearer
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '503':
          $ref: '#/components/responses/AuthenticationUnavailable'

  /presence:
    get:
      summary: Current PIR presence state
      security:
        - bearerAuth: []
      responses:
        '200':
          description: PIR presence state
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Presence'
        '401':
          $ref: '#/components/responses/UnauthorizedSession'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '503':
          description: PIR presence state or authentication service is unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /access-requests:
    post:
      summary: Submit an access request
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AccessRequestCreate'
      responses:
        '202':
          description: Request accepted in pending or busy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessRequestStatus'
        '401':
          $ref: '#/components/responses/UnauthorizedSession'
        '403':
          description: PIR presence is absent or the UUID belongs to a different session
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: UUID already submitted by this session, with the existing status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessRequestStatus'
        '422':
          $ref: '#/components/responses/InvalidRequest'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '503':
          description: Controller, PIR presence state, or authentication service is unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /access-requests/{request_id}:
    get:
      summary: Poll the state and result of an access request
      security:
        - bearerAuth: []
      parameters:
        - name: request_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Current state, with the result once complete
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessRequestStatus'
        '401':
          $ref: '#/components/responses/UnauthorizedSession'
        '403':
          description: The UUID belongs to a different session
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Request UUID not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          $ref: '#/components/responses/InvalidRequest'
        '429':
          $ref: '#/components/responses/TooManyRequests'
        '503':
          description: Controller or authentication service is unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
State machine
- present is the app state after GET /presence reports presence, before
  the app submits a request.
- pending means the request is next in the queue or is already running.
- busy means another operation has the turn or another request is ahead
  in the queue.
- complete means the operation ended and its result is available.
- expired means the queue deadline passed before execution started.
A new request requires active PIR presence. When presence is active, the
controller can accept and queue a request while another operation has the
turn. The controller processes one operation at a time and checks presence
again before taking the next request.

If the owning session repeats a UUID, POST /access-requests returns 409
with the current status and keeps the original queue entry. The owning
session can poll the request until it reaches complete or expired. Use
the same UUID when retrying a submission. The dispatcher retains request
IDs and results in memory for the lifetime of the controller process.
```mermaid
stateDiagram-v2
    [*] --> present: PIR reports presence
    present --> [*]: presence lost before submission
    present --> pending: request accepted with controller available
    present --> busy: request accepted while another operation has the turn
    pending --> busy: another operation takes the controller
    busy --> pending: controller available and request is next
    pending --> complete: operation ended and result is available
    pending --> expired: queue deadline reached before execution
    busy --> expired: queue deadline reached before execution
    complete --> [*]: app returns to standby
    expired --> [*]: app shows timeout and returns to standby
```
Timing
- Session lifetime is 10 minutes (DURACION_SESION_MINUTOS in
  autenticacion.py).
- Queue timeout is 10 seconds from acceptance. Once the controller takes
  a request, the request keeps its turn until the operation ends and the
  controller returns to standby.
- Network response time has a target of under 2 seconds per HTTP round
  trip, per NFR-14.
Running the mobile API on the Raspberry Pi
From the repository root, use the Python environment that already runs
the Raspberry Pi controller.
python3 -m pip install -r requirements-mobile-api.txt
Set API_HOST to the Raspberry Pi's LAN IP address. Set API_CERT and
API_KEY to the server certificate and private key paths. Keep the private
key outside the repository.
python3 src/Main_code.py --solo-botones \
  --api-host "$API_HOST" \
  --api-cert "$API_CERT" \
  --api-key "$API_KEY"
Omit --solo-botones to use the graphical controller. In either mode, the API
listens on HTTPS port 8000 and shares the active controller's dispatcher.
Android connects to https://raspberrypi.local:8000/ using the certificate
trust configuration described in [Mobile API security](mobile_security.md).
Endpoint responses
Endpoint	Success	Other responses
POST /sessions	200 with token and expira	401, 422, 429, 503
DELETE /sessions	204 with no body, including on repeat requests	401, 503
GET /presence	200 with present: true or present: false	401, 429, 503
POST /access-requests	202 with the queued request status	401, 403, 409, 422, 429, 503
GET /access-requests/{request_id}	200 with the request status and result	401, 403, 404, 422, 429, 503


The API returns a generic error message for malformed requests (422).
Rate-limited responses (429) include Retry-After in seconds.
Verification
The 20 API tests passed on macOS. A separate localhost test verified HTTPS
with a temporary certificate and a simulated controller. Verification on
the Raspberry Pi with its certificate, PIR and servo is pending.