import asyncio
import unittest

import flet as ft

from app.ui.views.recordings_view import RecordingsPage


class FakePubSub:
    def subscribe_topic(self, *_args, **_kwargs):
        return None


class FakePage:
    def __init__(self, width=320):
        self.pubsub = FakePubSub()
        self.width = width
        self.on_keyboard_event = None
        self.on_resized = None

    def run_task(self, *_args, **_kwargs):
        return None

    def update(self):
        return None


class FakeLanguageManager:
    def __init__(self):
        self.language = {
            "recordings_page": {},
            "recording_dialog": {},
            "base": {},
            "video_quality": {},
        }

    def add_observer(self, *_args, **_kwargs):
        return None


class FakeSettings:
    def __init__(self):
        self.user_config = {"is_grid_view": True}


class FakeApp:
    def __init__(self, is_mobile=True, width=320):
        self.is_mobile = is_mobile
        self.page = FakePage(width=width)
        self.language_manager = FakeLanguageManager()
        self.settings = FakeSettings()
        self.content_area = ft.Column()


class RecordingsPageTests(unittest.TestCase):
    def test_mobile_single_column_layout_uses_list_view(self):
        app = FakeApp(is_mobile=True, width=320)
        page = RecordingsPage(app)
        page.recording_card_area.content.update = lambda: None

        asyncio.run(page.recalculate_grid_columns())

        list_view = page.recording_card_area.content
        self.assertIsInstance(list_view, ft.ListView)
        self.assertEqual(list_view.spacing, 10)


if __name__ == "__main__":
    unittest.main()
