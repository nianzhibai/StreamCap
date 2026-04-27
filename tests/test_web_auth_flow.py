import unittest
from datetime import datetime, timedelta, timezone

from main import resolve_web_auth_state


class FakeConfigManager:
    def __init__(self, login_required=False):
        self.login_required = login_required

    def get_config_value(self, key, default=None):
        if key == "login_required":
            return self.login_required
        return default


class FakeAuthManager:
    def __init__(self):
        self.active_sessions = {}

    def validate_session(self, session_token):
        return session_token in self.active_sessions


class ResolveWebAuthStateTests(unittest.TestCase):
    def test_returns_admin_when_secure_login_is_disabled(self):
        config_manager = FakeConfigManager(login_required=False)
        auth_manager = FakeAuthManager()

        should_login, username = resolve_web_auth_state(config_manager, auth_manager, None)

        self.assertFalse(should_login)
        self.assertEqual(username, "admin")

    def test_requires_login_without_valid_session_when_enabled(self):
        config_manager = FakeConfigManager(login_required=True)
        auth_manager = FakeAuthManager()

        should_login, username = resolve_web_auth_state(config_manager, auth_manager, None)

        self.assertTrue(should_login)
        self.assertIsNone(username)

    def test_reloads_latest_login_required_value_on_each_check(self):
        config_manager = FakeConfigManager(login_required=False)
        auth_manager = FakeAuthManager()

        first_result = resolve_web_auth_state(config_manager, auth_manager, None)
        config_manager.login_required = True
        second_result = resolve_web_auth_state(config_manager, auth_manager, None)

        self.assertEqual(first_result, (False, "admin"))
        self.assertEqual(second_result, (True, None))

    def test_allows_access_with_valid_session_when_enabled(self):
        config_manager = FakeConfigManager(login_required=True)
        auth_manager = FakeAuthManager()
        token = "session-token"
        auth_manager.active_sessions[token] = {
            "username": "alice",
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=31),
        }

        should_login, username = resolve_web_auth_state(config_manager, auth_manager, token)

        self.assertFalse(should_login)
        self.assertEqual(username, "alice")


if __name__ == "__main__":
    unittest.main()
