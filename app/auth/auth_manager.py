import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..utils.logger import logger


class AuthManager:
    SESSION_DURATION = timedelta(days=31)
    
    def __init__(self, app):
        self.app = app
        self.config_manager = app.config_manager
        self.is_authenticated = False
        self.session_token = None
        self.active_sessions = {}
    
    async def initialize(self):
        web_auth = self.config_manager.load_web_auth_config()
        
        if not web_auth.get("users"):
            default_username = "admin"
            default_password = "admin"
            
            salt = secrets.token_hex(8)
            hashed_password = self._hash_password(default_password, salt)
            
            web_auth["users"] = [{
                "username": default_username,
                "password_hash": hashed_password,
                "salt": salt,
                "is_admin": True
            }]
            
            await self.config_manager.save_web_auth_config(web_auth)
            logger.info("Default account created: admin/admin")
    
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
    
    async def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        web_auth = self.config_manager.load_web_auth_config()
        users = web_auth.get("users", [])
        
        for i, user in enumerate(users):
            if user["username"] == username:
                salt = user["salt"]
                hashed_old_password = self._hash_password(old_password, salt)
                
                if hashed_old_password == user["password_hash"]:
                    new_salt = secrets.token_hex(8)
                    hashed_new_password = self._hash_password(new_password, new_salt)
                    
                    web_auth["users"][i]["password_hash"] = hashed_new_password
                    web_auth["users"][i]["salt"] = new_salt
                    
                    await self.config_manager.save_web_auth_config(web_auth)
                    return True
        
        return False 
