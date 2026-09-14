# API v1 usage (minimal)

Base path: `/api/v1/`

## Auth
POST `/api/v1/auth/token/`
```json
{"email": "user@example.com", "password": "..."}
```
Response: `{"token": "...", "user_id": "...", "email": "..."}`

Header: `Authorization: Token <token>`

## Tenant scope
Required for resource endpoints:
`X-Organization-ID: <uuid>`

Optional alternative: `X-Organization-Slug: <slug>`

## Endpoints
- `GET /me/`
- `GET /organizations/`
- `GET /subscriptions/`
- `GET /invoices/`
- `GET /invoices/<uuid>/`
- `GET /licenses/`
- `GET|POST /tickets/`
- `GET /tickets/<uuid>/`
