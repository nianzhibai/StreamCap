import unittest

import flet as ft

from app.models.recording.recording_model import Recording
from app.ui.components.business.recording_card import RecordingCardManager


class FakePubSub:
    def subscribe_topic(self, *_args, **_kwargs):
        return None


class FakePage:
    def __init__(self):
        self.pubsub = FakePubSub()
        self.theme_mode = ft.ThemeMode.LIGHT

    def run_task(self, *_args, **_kwargs):
        return None


class FakeLanguageManager:
    def __init__(self):
        self.language = {
            "recording_card": {
                "edit_record_config": "Edit",
                "preview_video": "Preview",
                "delete_monitor": "Delete",
                "open_folder": "Open Folder",
                "recording_info": "Info",
                "stop_record": "Stop Record",
                "start_record": "Start Record",
                "stop_monitor": "Stop Monitor",
                "start_monitor": "Start Monitor",
                "recording": "Recording",
                "recording_error": "Recording Error",
                "live_broadcasting": "Live",
                "offline": "Offline",
                "no_monitor": "Stopped",
                "checking": "Checking",
                "live_room": "Live Room",
            },
            "recording_manager": {
                "monitor_stopped": "Stopped",
            },
            "base": {},
            "recordings_page": {},
            "video_quality": {},
            "storage_page": {},
        }

    def add_observer(self, *_args, **_kwargs):
        return None


class FakeRecordManager:
    def get_duration(self, _recording):
        return "00:00:00"


class FakeApp:
    def __init__(self, is_mobile):
        self.is_mobile = is_mobile
        self.page = FakePage()
        self.language_manager = FakeLanguageManager()
        self.record_manager = FakeRecordManager()


class RecordingCardManagerTests(unittest.TestCase):
    def test_mobile_action_row_wraps_to_keep_monitor_button_visible(self):
        app = FakeApp(is_mobile=True)
        manager = RecordingCardManager(app)
        recording = Recording(
            rec_id="rec-1",
            url="https://example.com/live",
            streamer_name="主播",
            record_format="TS",
            quality="OD",
            segment_record=False,
            segment_time="1800",
            monitor_status=False,
            scheduled_recording=False,
            scheduled_start_time="",
            monitor_hours="",
            recording_dir=None,
            enabled_message_push=False,
            only_notify_no_record=False,
            flv_use_direct_download=False,
        )

        card_data = manager._create_card_components(recording)
        action_row = card_data["card"].content.content.controls[3]

        self.assertTrue(action_row.wrap)
        self.assertEqual(len(action_row.controls), 7)


if __name__ == "__main__":
    unittest.main()
