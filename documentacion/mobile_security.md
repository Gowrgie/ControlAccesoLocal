# Mobile API security

## TLS and network access

- LAC-99 must serve the mobile API over HTTPS with TLS 1.2 or newer at
  `https://raspberrypi.local:8000`.
- The API must be reachable only from the local network. The deployment
  must block access from outside that network.
- Use a certificate issued by the project's private CA. The server
  certificate must include `raspberrypi.local` as a DNS name in its
  Subject Alternative Name extension.
- Configure Android to trust the public CA certificate for
  `raspberrypi.local` and disable cleartext HTTP. Android must reject
  invalid, expired, or mismatched server certificates.
- Keep the CA and server private keys out of the Android app and Git.

## Mobile sessions

- `POST /sessions` creates a token with a fixed lifetime of 10 minutes.
  The database stores the token hash and its expiration timestamp.
- The client sends the token in the `Authorization: Bearer <token>`
  header. Tokens must be kept out of URLs and application logs.
- The API validates the token on each protected request. A missing,
  invalid, or expired token returns `401 Unauthorized`.
- `DELETE /sessions` revokes the session by deleting its stored token
  hash and returns `204 No Content` even if the session is already gone.

## Rate limiting

The HTTP service must enforce these configurable limits over a rolling
60-second window.

| Endpoint | Limit | Scope |
| --- | --- | --- |
| `POST /sessions` | 10 login attempts | Source IP |
| `POST /sessions` | 5 failed login attempts | Login identifier |
| `POST /access-requests` | 10 submissions | Authenticated user |
| `GET /presence` and `GET /access-requests/{request_id}` | 120 requests combined | Authenticated session |

Apply both login limits. Use the same failed-login policy for known and
unknown identifiers. Count submitted access requests, including retries,
against the submission limit. The dispatcher still deduplicates retries
by request UUID.

When a limit is reached, return `429 Too Many Requests` with a
`Retry-After` header containing the number of seconds until the request
can be retried. Rejected requests do not extend the waiting period.
The Android client must wait for that interval before retrying.