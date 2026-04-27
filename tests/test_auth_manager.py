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


if __name__ == "__main__":
    unittest.main()
