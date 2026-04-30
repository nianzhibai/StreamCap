import copy
import os
import unittest
from unittest.mock import patch

from app.ui.views.settings_view import SettingsPage


class FakePage:
    def __init__(self):
        self.on_keyboard_event = None

    def run_task(self, *_args, **_kwargs):
        return None


class FakeConfigManager:
    def __init__(self):
        self.user_config_data = {"language": "Chinese", "login_required": False}
        self.language_config_data = {"Chinese": "zh_CN"}
        self.default_config_data = {"login_required": False}
        self.cookies_config_data = {}
        self.accounts_config_data = {}

    def load_user_config(self):
        return copy.deepcopy(self.user_config_data)

    def load_language_config(self):
        return copy.deepcopy(self.language_config_data)

    def load_default_config(self):
        return copy.deepcopy(self.default_config_data)

    def load_cookies_config(self):
        return copy.deepcopy(self.cookies_config_data)

    def load_accounts_config(self):
        return copy.deepcopy(self.accounts_config_data)


class FakeApp:
    def __init__(self):
        self.page = FakePage()
        self.config_manager = FakeConfigManager()
        self.content_area = object()


class SettingsPageTests(unittest.TestCase):
    def test_refresh_runtime_configs_reads_latest_login_required_value(self):
        app = FakeApp()
        settings_page = SettingsPage(app)

        self.assertFalse(settings_page.user_config["login_required"])

        app.config_manager.user_config_data["login_required"] = True
        settings_page.refresh_runtime_configs()

        self.assertTrue(settings_page.user_config["login_required"])

    def test_refresh_runtime_configs_applies_login_required_env_override(self):
        app = FakeApp()

        with patch.dict(os.environ, {"LOGIN_REQUIRED": "true"}):
            settings_page = SettingsPage(app)

        self.assertTrue(settings_page.user_config["login_required"])


if __name__ == "__main__":
    unittest.main()
