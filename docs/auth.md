# Auth Pattern

This document describes the authentication architecture pattern to follow when implementing auth in Flux.

---

## Backend — `apps/authentication`

Same 4-layer structure as every other app (`api → service → repository → serializer`), split into sub-folders by concern:

```
api/v1/
  auth/          # login, register, forgot/reset password
  account/       # me, change-password, switch-org
  mfa/
    setup/       # totp + sms setup flows
    login/       # mfa login flow (send-otp, verify)
    manage/      # status, disable
```

**One file = one APIView.**

---

### API Layer Pattern

The API layer only validates input, delegates to the service, and maps exceptions to HTTP status codes:

```python
# login_api.py — the full pattern
serializer = LoginSerializer(data=request.data)
serializer.is_valid(raise_exception=True)
try:
    result = AuthService().login(...)
except PermissionError as exc:
    return Response({"error": str(exc)}, status=403)
except ValueError as exc:
    return Response({"error": str(exc)}, status=401)
return Response(result, status=200)
```

---

### JWT

Uses `rest_framework_simplejwt`. `AuthService._build_token_response()` is the **single place that mints tokens**. The `/auth/refresh/` endpoint is wired directly to simplejwt's `TokenRefreshView` — no custom code needed there.

---

### MFA Flow

When MFA is enabled, login returns a short-lived (5 min) **pre-auth JWT** with a custom `mfa_pending: true` claim instead of real tokens. The client uses that token to call `/auth/mfa/verify/`, which mints the real access + refresh tokens only after the code passes.

The pre-auth token is validated inside `MFAService._user_from_preauth_token()` — it checks for the `mfa_pending` claim to prevent a regular access token from being used at this endpoint.

**Other MFA details:**
- `MFAService` is a singleton (`__new__` pattern)
- Backup codes are SHA-256 hashed, single-use, and deleted on consumption

---

## Frontend — 3-Piece Pattern

| Piece | File | Role |
|---|---|---|
| API calls | `services/authApi.js` | Thin wrappers over axios, one per endpoint |
| State | `stores/authStore.js` | Zustand — holds user, org, MFA state; access token in-memory only |
| Bootstrap | `features/auth/AuthProvider.jsx` | Runs `bootstrap()` on mount, blocks render until resolved |

---

### Token Storage

- Access token — in-memory (`let` in `authStore.js`), **never localStorage**
- Refresh token — `Secure; SameSite=Strict` cookie (`_rt`)

---

### MFA Login State

`mfaPending`, `mfaToken`, `mfaMethod` live in the store during the MFA flow and are cleared after `verifyMFA()` or `logout()`.

---

### Refresh / 401 Recovery

Handled entirely in `services/api.js` with a queue: if a 401 fires, all in-flight requests are queued while one token refresh is attempted, then replayed or rejected together.

---

## Login Flow (Full Sequence)

```
POST /auth/login/
  → MFA disabled → { access, refresh, user, orgs }  ← full JWT, done
  → MFA enabled  → { requires_mfa, mfa_token, mfa_method }

  (store sets mfaPending=true, holds mfa_token)

POST /auth/mfa/verify/  { mfa_token, code }
  → { access, refresh, user, orgs }  ← full JWT, MFA cleared
```

---

## Endpoints Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/login/` | Email + password login |
| `POST` | `/auth/register/` | Create account |
| `POST` | `/auth/refresh/` | Rotate access token (simplejwt native) |
| `POST` | `/auth/forgot-password/` | Send reset email |
| `POST` | `/auth/reset-password/` | Consume reset token, set new password |
| `GET` | `/auth/me/` | Return current user + orgs |
| `POST` | `/auth/change-password/` | Authenticated password change |
| `POST` | `/auth/mfa/setup/totp/` | Begin TOTP setup |
| `POST` | `/auth/mfa/setup/sms/` | Begin SMS setup |
| `POST` | `/auth/mfa/login/send-otp/` | Send SMS OTP during login |
| `POST` | `/auth/mfa/verify/` | Verify MFA code, return full JWT |
| `GET` | `/auth/mfa/manage/status/` | MFA enabled/methods |
| `POST` | `/auth/mfa/manage/disable/` | Disable MFA |
