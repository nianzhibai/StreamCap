# Web Username Change Design

## Goal

Add username change support to the web security settings page.

## Scope

- Add a username change form to the existing web security settings tab.
- Reject empty usernames, unchanged usernames, and duplicate usernames.
- After a successful username change, invalidate existing sessions for that account and require login again with the new username.

## Design

### Auth behavior

- Add `change_username(current_username, new_username)` to `AuthManager`.
- Return explicit result codes for:
  - success
  - user not found
  - username already exists
- On success, update the matching user record in `config/web_auth.json`.
- Invalidate all in-memory sessions belonging to the renamed account so all tabs are forced back through login.

### UI behavior

- Keep the existing security settings page.
- Add a new username input and a button below the current username display.
- On success:
  - show a success message
  - remove `session_token` from browser storage
  - clear the current page and show the login page
- The next login must use the new username.

## Testing

Add unit coverage for:

- successful username change
- duplicate username rejection
- authentication moves from old username to new username after the change
