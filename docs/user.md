# User Pattern

This document describes the user model and architecture pattern to follow when implementing user accounts in Flux.

---

## Backend

### Model — `apps/users/models.py`

`User` extends `AbstractBaseUser` + `PermissionsMixin`.

**Key fields:**
- UUID primary key
- `email` as `USERNAME_FIELD`
- `initials` and `is_profile_complete` are **computed on every `.save()`** — never set them manually
- `password_reset_token_jti` on the user itself is used to invalidate password reset tokens

**Related models:**
- `UserMFASettings` — OneToOne on User, holds MFA configuration
- `MFAOTPCode` — SMS OTPs, separate model

---

### 4-Layer Stack

Every domain (including users) follows this exact structure:

| Layer | File | Responsibility |
|---|---|---|
| API | `api/v1/user_detail_api.py` | HTTP in/out, permission checks, calls service |
| Service | `services/user_service.py` | Business logic, owns permission decisions |
| Repository | `repositories/user_repository.py` | All DB queries, nothing else |
| Serializer | `serializers/user_serializers.py` | Validation + DTO shapes |

**Rules:**
- Services throw exceptions; the API layer catches them and maps to HTTP status codes
- Repository only does queries — no business logic ever

---

### Permissions — `apps/core/permissions/base.py`

Every view uses one of four permission classes. They check whether an active `OrgMembership` exists for `(X-Org-Id, request.user, role)`.

```python
permission_classes = [IsAuthenticated, IsGPAdmin]  # composable
```

---

## Frontend

### Store — `stores/authStore.js`

Zustand store holds `user`, `currentOrg`, `orgs`, and MFA state.

**Token storage:**
- Access token is **in-memory** (module-level `let`) — never `localStorage`
- Refresh token is in a `Secure; SameSite=Strict` cookie (`_rt`)

---

### Hook — `features/auth/useAuth.js`

Thin selector hook. Every component imports `useAuth()` — never the store directly. Single access point for user state.

```js
const { user, currentOrg } = useAuth()
```

---

### Bootstrap — `features/auth/AuthProvider.jsx`

Wraps the whole app. On mount calls `bootstrap()` which refreshes the token and rehydrates `user` + `currentOrg` from the server. Blocks render until done.

---

### Route Guard — `features/auth/ProtectedRoute.jsx`

Wraps every protected route. Derives `portalRole` (`'gp'` or `'lp'`) from `currentOrg.role` and redirects if the role doesn't match `allowedRoles`.

```jsx
<ProtectedRoute allowedRoles={['gp']}>
  <GPDashboard />
</ProtectedRoute>
```

---

## Flow Summary

```
App load → AuthProvider.bootstrap() → refresh token → /auth/me → hydrate store
                                                                       ↓
                                                         ProtectedRoute derives portalRole
                                                                       ↓
                                                         component calls useAuth()
```
