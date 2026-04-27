# Web Username Change Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let web users change their username from the security settings page and force re-login with the new username.

**Architecture:** Extend `AuthManager` with an explicit username change API and session invalidation for the renamed account. Reuse the existing web login page and security settings tab instead of adding a new page.

**Tech Stack:** Python 3.10+, `unittest`, Flet, existing web auth config JSON

---

### Task 1: Cover Username Change Rules

**Files:**
- Modify: `tests/test_auth_manager.py`
- Modify: `app/auth/auth_manager.py`

- [ ] Step 1: Add failing tests for successful rename, duplicate rejection, and authentication migration.
- [ ] Step 2: Run `venv/bin/python -m unittest tests.test_auth_manager -v` and confirm the new username tests fail before implementation.
- [ ] Step 3: Add minimal `change_username()` support and session invalidation logic.
- [ ] Step 4: Re-run `venv/bin/python -m unittest tests.test_auth_manager -v` and confirm the tests pass.

### Task 2: Add Security Settings Controls

**Files:**
- Modify: `app/ui/views/settings_view.py`
- Modify: `app/ui/views/login_view.py`
- Modify: `locales/zh_CN.json`
- Modify: `locales/en.json`

- [ ] Step 1: Add new username field, validation, and button to the web security tab.
- [ ] Step 2: Clear the current browser token and return the user to the login page after a successful rename.
- [ ] Step 3: Add localized UI copy for the new field and messages.

### Task 3: Verify Final State

**Files:**
- Verify only

- [ ] Step 1: Run `venv/bin/python -m unittest tests.test_auth_manager -v`.
- [ ] Step 2: Run `venv/bin/python -m compileall app/auth/auth_manager.py app/ui/views/settings_view.py app/ui/views/login_view.py main.py`.
- [ ] Step 3: Review the diff to confirm the change only affects username change flow and forced relogin behavior.
