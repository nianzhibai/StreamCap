import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from ..utils.logger import logger


class GlobalAuthState:
    active_sessions: dict[str, dict[str, Any]] = {}


class AuthManager:
    SESSION_DURATION = timedelta(days=31)
    
    def __init__(self, app):
        self.app = app
        self.config_manager = app.config_manager
        self.is_authenticated = False
        self.session_token = None
        self.active_sessions = GlobalAuthState.active_sessions
    
    async def initialize(self):
        web_auth = self.config_manager.load_web_auth_config()

        if not web_auth.get("users"):
            username = self._get_env_value("WEB_AUTH_USERNAME") or "admin"
            password = self._get_env_value("WEB_AUTH_PASSWORD") or "admin"
            web_auth["users"] = [self._build_user_config(username, password, is_admin=True)]
            await self.config_manager.save_web_auth_config(web_auth)
            logger.info("Default web auth account created")
            return

        if self._apply_env_credentials(web_auth):
            await self.config_manager.save_web_auth_config(web_auth)
            logger.info("Web auth account updated from environment configuration")

    @staticmethod
    def _get_env_value(name: str) -> str | None:
        value = os.getenv(name)
        if value is None:
            return None
        stripped_value = value.strip()
        return stripped_value or None

    def _build_user_config(self, username: str, password: str, is_admin: bool) -> dict[str, Any]:
        salt = secrets.token_hex(8)
        return {
            "username": username,
            "password_hash": self._hash_password(password, salt),
            "salt": salt,
            "is_admin": is_admin,
        }

    def _apply_env_credentials(self, web_auth: dict[str, Any]) -> bool:
        username = self._get_env_value("WEB_AUTH_USERNAME")
        password = self._get_env_value("WEB_AUTH_PASSWORD")
        if not username and not password:
            return False

        users = web_auth.get("users", [])
        target_user = next((user for user in users if user.get("is_admin")), users[0])
        changed = False

        if username and target_user.get("username") != username:
            target_user["username"] = username
            changed = True

        if password:
            new_salt = secrets.token_hex(8)
            target_user["password_hash"] = self._hash_password(password, new_salt)
            target_user["salt"] = new_salt
            changed = True

        return changed
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Use SHA-256 and salt to hash password"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_session_token(self) -> str:
        """Generate session token"""
        return secrets.token_hex(16)

    def _build_session_info(self, username: str, is_admin: bool) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc)
        return {
            "username": username,
            "is_admin": is_admin,
            "created_at": created_at,
            "expires_at": created_at + self.SESSION_DURATION,
        }

    def _invalidate_sessions_for_username(self, username: str) -> None:
        invalid_tokens = [
            token for token, session in self.active_sessions.items()
            if session.get("username") == username
        ]
        for token in invalid_tokens:
            self.active_sessions.pop(token, None)
    
    async def authenticate(self, username: str, password: str) -> tuple[bool, Optional[str]]:
        web_auth = self.config_manager.load_web_auth_config()
        users = web_auth.get("users", [])
        
        for user in users:
            if user["username"] == username:
                salt = user["salt"]
                hashed_password = self._hash_password(password, salt)
                
                if hashed_password == user["password_hash"]:
                    session_token = self._generate_session_token()
                    self.active_sessions[session_token] = self._build_session_info(
                        username=username,
                        is_admin=user.get("is_admin", False),
                    )
                    return True, session_token
        
        return False, None
    
    def validate_session(self, session_token: str) -> bool:
        """Validate session token"""
        session_info = self.active_sessions.get(session_token)
        if not session_info:
            return False

        expires_at = session_info.get("expires_at")
        if not isinstance(expires_at, datetime):
            self.active_sessions.pop(session_token, None)
            return False

        if expires_at <= datetime.now(timezone.utc):
            self.active_sessions.pop(session_token, None)
            return False

        return True
    
    def logout(self, session_token: str) -> bool:
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False
    
    async def change_password(self, username: str, new_password: str) -> bool:
        web_auth = self.config_manager.load_web_auth_config()
        users = web_auth.get("users", [])
        
        for i, user in enumerate(users):
            if user["username"] == username:
                new_salt = secrets.token_hex(8)
                hashed_new_password = self._hash_password(new_password, new_salt)

                web_auth["users"][i]["password_hash"] = hashed_new_password
                web_auth["users"][i]["salt"] = new_salt

                await self.config_manager.save_web_auth_config(web_auth)
                self._invalidate_sessions_for_username(username)
                return True
        
        return False

    async def change_username(
            self,
            current_username: str,
            new_username: str
    ) -> Literal["success", "user_not_found", "username_exists"]:
        web_auth = self.config_manager.load_web_auth_config()
        users = web_auth.get("users", [])

        if any(user["username"] == new_username for user in users):
            return "username_exists"

        for user in users:
            if user["username"] == current_username:
                user["username"] = new_username
                await self.config_manager.save_web_auth_config(web_auth)
                self._invalidate_sessions_for_username(current_username)
                return "success"

        return "user_not_found"
