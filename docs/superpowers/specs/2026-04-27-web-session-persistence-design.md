# Web Session Persistence Design

## Goal

Allow web users to stay logged in across closing and reopening the page without re-entering credentials, while keeping the current behavior that a server restart invalidates all sessions.

## Scope

- Persist successful web login across browser refreshes, tab closes, and reopening the same site.
- Default session lifetime is 31 days.
- Multiple tabs may share the same logged-in session.
- Server restart still clears all sessions.

## Current State

- `LoginPage.handle_login()` stores `session_token` in `page.client_storage`.
- `main.py` reads `session_token` from `page.client_storage` on web startup.
- `AuthManager.active_sessions` stores sessions only in memory.
- `AuthManager.validate_session()` currently checks only whether the token exists in memory.

This means login restore works only while the in-memory session is still present and there is no explicit expiration model.

## Design

### Session model

Keep using in-memory sessions in `AuthManager.active_sessions`, but expand each entry to include:

- `username`
- `is_admin`
- `created_at`
- `expires_at`

`expires_at` is set to 31 days after authentication by default.

### Validation flow

- On successful login, create a new token and save the full session payload in memory.
- Continue storing the token in `page.client_storage`.
- On subsequent page loads, read `session_token` from `page.client_storage`.
- Accept the session only if the token exists and `expires_at` is still in the future.
- If the token is expired, remove it from `active_sessions` and treat the user as logged out.

### Multi-tab behavior

Do not invalidate older sessions for the same account. Multiple tabs and browser windows may reuse the same token while it is valid.

### Non-goals

- Persist sessions to disk
- Restore sessions after process restart
- Add refresh tokens or sliding expiration

## Testing

Add unit coverage for:

- fresh session tokens are valid immediately after login
- expired session tokens are rejected and removed from memory
