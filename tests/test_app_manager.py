import unittest
from types import SimpleNamespace
from unittest.mock import patch

import flet as ft

from app.app_manager import App


class FakePage:
    def run_task(self, *_args, **_kwargs):
        return None


class FakeSettingsPage:
    def __init__(self, _app):
        self.user_config = {}
        self.language_code = "zh_CN"


class FakeLanguageManager:
    def __init__(self, _app):
        self.language = {}


class RecordingPageRequiresIsMobile:
    def __init__(self, app):
        if not hasattr(app, "is_mobile"):
            raise AttributeError("App.is_mobile must exist before RecordingsPage initializes")


class FakeRecordingManager:
    def __init__(self, _app):
        self.check_free_space = object()
        self.loop_time_seconds = 180


class FakeInstallationManager:
    def __init__(self, _app):
        self.check_env = object()


class FakeUpdateChecker:
    def __init__(self, _app):
        self.update_config = {"auto_check": False, "check_interval": 0}


class AppManagerTests(unittest.TestCase):
    def test_app_sets_is_mobile_before_recordings_page_initializes(self):
        with (
            patch("app.app_manager.AsyncProcessManager", return_value=SimpleNamespace()),
            patch("app.app_manager.ConfigManager", return_value=SimpleNamespace()),
            patch("app.app_manager.SettingsPage", FakeSettingsPage),
            patch("app.app_manager.LanguageManager", FakeLanguageManager),
            patch("app.app_manager.AboutPage", side_effect=lambda app: SimpleNamespace(app=app)),
            patch("app.app_manager.RecordingsPage", RecordingPageRequiresIsMobile),
            patch("app.app_manager.HomePage", side_effect=lambda app: SimpleNamespace(app=app)),
            patch("app.app_manager.StoragePage", side_effect=lambda app: SimpleNamespace(app=app)),
            patch("app.app_manager.NavigationSidebar", side_effect=lambda app: ft.Container()),
            patch("app.app_manager.LeftNavigationMenu", side_effect=lambda app: ft.Container()),
            patch("app.app_manager.ShowSnackBar", side_effect=lambda app: SimpleNamespace(app=app)),
            patch("app.app_manager.RecordingCardManager", side_effect=lambda app: SimpleNamespace(app=app)),
            patch("app.app_manager.RecordingManager", FakeRecordingManager),
            patch("app.app_manager.InstallationManager", FakeInstallationManager),
            patch("app.app_manager.UpdateChecker", FakeUpdateChecker),
            patch("app.app_manager.utils.get_startup_info", return_value=None),
        ):
            app = App(FakePage())

        self.assertFalse(app.is_mobile)


if __name__ == "__main__":
    unittest.main()
