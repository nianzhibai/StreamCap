import unittest
from datetime import datetime, timedelta, timezone

from app.auth.auth_manager import AuthManager


class FakeConfigManager:
    def __init__(self):
        self.web_auth = {
            "users": [
                {
                    "username": "admin",
                    "password_hash": "",
                    "salt": "testsalt",
                    "is_admin": True,
                }
            ]
        }

    def load_web_auth_config(self):
        return self.web_auth

    async def save_web_auth_config(self, config):
        self.web_auth = config


class FakeApp:
    def __init__(self):
        self.config_manager = FakeConfigManager()


class AuthManagerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FakeApp()
        self.manager = AuthManager(self.app)
        self.manager.active_sessions.clear()
        user = self.app.config_manager.web_auth["users"][0]
        user["password_hash"] = self.manager._hash_password("admin", user["salt"])

    async def test_authenticate_creates_31_day_session_metadata(self):
        success, token = await self.manager.authenticate("admin", "admin")

        self.assertTrue(success)
        self.assertIsNotNone(token)

        session = self.manager.active_sessions[token]
        self.assertEqual(session["username"], "admin")
        self.assertIn("created_at", session)
        self.assertIn("expires_at", session)
        self.assertGreater(session["expires_at"], session["created_at"])

        ttl = session["expires_at"] - session["created_at"]
        self.assertEqual(ttl, timedelta(days=31))
        self.assertTrue(self.manager.validate_session(token))

    async def test_validate_session_rejects_and_cleans_expired_session(self):
        token = "expired-token"
        self.manager.active_sessions[token] = {
            "username": "admin",
            "is_admin": True,
            "created_at": datetime.now(timezone.utc) - timedelta(days=32),
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
        }

        self.assertFalse(self.manager.validate_session(token))
        self.assertNotIn(token, self.manager.active_sessions)

    async def test_session_remains_valid_across_new_auth_manager_instances(self):
        success, token = await self.manager.authenticate("admin", "admin")

        self.assertTrue(success)
        self.assertTrue(self.manager.validate_session(token))

        second_manager = AuthManager(FakeApp())

        self.assertTrue(second_manager.validate_session(token))
        self.assertEqual(
            second_manager.active_sessions[token]["username"],
            "admin",
        )

    async def test_change_username_updates_auth_record_and_invalidates_sessions(self):
        success, token = await self.manager.authenticate("admin", "admin")

        self.assertTrue(success)
        self.assertTrue(self.manager.validate_session(token))

        result = await self.manager.change_username("admin", "streamcap")

        self.assertEqual(result, "success")
        self.assertFalse(self.manager.validate_session(token))
        self.assertNotIn(token, self.manager.active_sessions)
        self.assertEqual(
            self.app.config_manager.web_auth["users"][0]["username"],
            "streamcap",
        )

        old_success, _ = await self.manager.authenticate("admin", "admin")
        new_success, new_token = await self.manager.authenticate("streamcap", "admin")
        self.assertFalse(old_success)
        self.assertTrue(new_success)
        self.assertIsNotNone(new_token)

    async def test_change_username_rejects_duplicate_username(self):
        self.app.config_manager.web_auth["users"].append(
            {
                "username": "existing",
                "password_hash": self.manager._hash_password("other", "othersalt"),
                "salt": "othersalt",
                "is_admin": False,
            }
        )

        result = await self.manager.change_username("admin", "existing")

        self.assertEqual(result, "username_exists")
        self.assertEqual(
            self.app.config_manager.web_auth["users"][0]["username"],
            "admin",
        )

    async def test_change_password_does_not_require_old_password_for_logged_in_user(self):
        login_success, token = await self.manager.authenticate("admin", "admin")

        self.assertTrue(login_success)
        self.assertTrue(self.manager.validate_session(token))

        success = await self.manager.change_password("admin", "new-password")

        self.assertTrue(success)
        self.assertFalse(self.manager.validate_session(token))
        self.assertNotIn(token, self.manager.active_sessions)

        old_success, _ = await self.manager.authenticate("admin", "admin")
        new_success, _ = await self.manager.authenticate("admin", "new-password")

        self.assertFalse(old_success)
        self.assertTrue(new_success)


if __name__ == "__main__":
    unittest.main()
