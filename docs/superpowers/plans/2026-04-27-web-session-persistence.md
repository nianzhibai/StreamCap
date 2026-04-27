# Web Session Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep web users logged in for 31 days across page reopenings while still invalidating sessions on server restart.

**Architecture:** Keep the existing browser-side token storage in `page.client_storage`, and extend server-side in-memory sessions with explicit creation and expiration timestamps. Validation remains centralized in `AuthManager`, so the startup login gate in `main.py` can keep using a single check.

**Tech Stack:** Python 3.10+, `unittest`, Flet, existing `AuthManager`

---

### Task 1: Cover Session Expiration Behavior

**Files:**
- Create: `tests/test_auth_manager.py`
- Modify: `app/auth/auth_manager.py`

- [ ] Step 1: Write a failing unit test for fresh and expired sessions.
- [ ] Step 2: Run `python -m unittest tests.test_auth_manager -v` and confirm the expiration test fails because session metadata does not yet contain expiry logic.
- [ ] Step 3: Add minimal session timestamp support in `AuthManager`.
- [ ] Step 4: Re-run `python -m unittest tests.test_auth_manager -v` and confirm the tests pass.

### Task 2: Wire Startup Validation To The New Session Rules

**Files:**
- Modify: `main.py`

- [ ] Step 1: Keep the current startup flow, but clear stale browser tokens when validation fails.
- [ ] Step 2: Re-run the auth manager tests plus a focused syntax check for the changed modules.

### Task 3: Verify Final Behavior

**Files:**
- Verify only

- [ ] Step 1: Run `python -m unittest tests.test_auth_manager -v`.
- [ ] Step 2: Run `python -m compileall app/auth/auth_manager.py main.py app/ui/views/login_view.py`.
- [ ] Step 3: Review the diff to confirm the change does not introduce disk-persisted sessions or single-login invalidation behavior.
