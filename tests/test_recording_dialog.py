import unittest
from unittest.mock import AsyncMock, patch

import flet as ft

from app.ui.components.business.recording_dialog import RecordingDialog
from app.utils.douyin_url_normalizer import DouyinNormalizationError


class FakeLanguageManager:
    def __init__(self):
        self.language = {
            "recording_dialog": {
                "input_live_link": "Enter Live Room URL",
                "example": "Example",
                "select_resolution": "Select Recording Resolution",
                "flv_use_direct_download": "FLV Source Use Direct Downloader",
                "flv_use_direct_download_tip": "Enable lower latency",
                "input_anchor_name": "Enter Broadcaster Name",
                "default_input": "Can be left blank",
                "select_record_format": "Select Recording Format",
                "input_save_path": "Enter Save Path for Recordings",
                "is_segment_enabled": "Enable Segmented Recording",
                "segment_record_time": "Segment Recording Time",
                "input_segment_time": "Enter Segment Time",
                "scheduled_recording": "Enable Daily Scheduled Monitoring",
                "scheduled_start_time": "Daily Monitoring Start Time",
                "monitor_hours": "Daily Monitoring Hours",
                "enable_message_push": "Enable Message Push",
                "only_notify_no_record": "Only notify without recording",
                "batch_input_tip": "Batch Input",
                "single_input": "Single Input",
                "batch_input": "Batch Input",
                "live_room": "Live Room",
                "platform_not_supported_tip": "This platform does not support recording",
                "douyin_parse_failed_tip": "Failed to parse Douyin link",
                "pick_time": "Pick time",
                "pick_time_tip": "Configure scheduled time",
                "time_out_of_range": "Time out of range",
                "pick_time_slot": "Pick your time slot",
                "hour_label_text": "Hour",
                "minute_label_text": "Minute",
                "select_media_type": "Select Media Type",
                "video": "Video",
                "audio": "Audio",
                "duplicate_url_title": "Duplicate Live Room URL",
                "duplicate_url_content": "The live room URL already exists",
            },
            "recordings_page": {
                "add_record": "Add Recording",
                "edit_record": "Edit Recording",
            },
            "base": {
                "yes": "Yes",
                "no": "No",
                "confirm": "Confirm",
                "cancel": "Cancel",
                "sure": "Sure",
                "close": "Close",
            },
            "video_quality": {
                "OD": "Original",
                "UHD": "Ultra",
                "HD": "High",
                "SD": "Standard",
                "LD": "Low",
            },
        }

    def add_observer(self, *_args, **_kwargs):
        return None


class FakeSnackBar:
    def __init__(self):
        self.messages = []

    async def show_snack_bar(self, message, **kwargs):
        self.messages.append((message, kwargs))


class FakePage:
    def __init__(self):
        self.overlay = []
        self.width = 1280
        self.theme_mode = ft.ThemeMode.LIGHT

    def update(self):
        return None

    def open(self, *_args, **_kwargs):
        return None


class FakeRecordManager:
    def __init__(self):
        self.recordings = []


class FakeRecording:
    def __init__(self, url):
        self.url = url


class FakeSettings:
    def __init__(self):
        self.user_config = {
            "enable_proxy": True,
            "proxy_address": "127.0.0.1:7890",
        }


class FakeApp:
    def __init__(self):
        self.is_mobile = False
        self.language_code = "en"
        self.page = FakePage()
        self.language_manager = FakeLanguageManager()
        self.record_manager = FakeRecordManager()
        self.settings = FakeSettings()
        self.snack_bar = FakeSnackBar()


class RecordingDialogSingleInputTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FakeApp()
        self.on_confirm_callback = AsyncMock()
        self.dialog = RecordingDialog(self.app, on_confirm_callback=self.on_confirm_callback)

    async def test_build_single_recording_payload_accepts_direct_douyin_room_url(self):
        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(return_value="https://live.douyin.com/845632139263"),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            recordings_info = await self.dialog._build_single_recording_payload(
                url_value="https://live.douyin.com/845632139263",
                streamer_name_value="主播",
                quality_value="OD",
                record_format_value="TS",
                recording_dir_value="",
                segment_visible=False,
                segment_time_value="1800",
                scheduled_recording_enabled=False,
                scheduled_start_time_values=["", ""],
                monitor_hours_values=["", ""],
                message_push_enabled=True,
                only_notify_no_record=False,
                flv_use_direct_download=False,
                rec_id=None,
                initial_values={},
            )

        self.assertEqual(recordings_info[0]["url"], "https://live.douyin.com/845632139263")
        normalize_mock.assert_awaited_once_with(
            "https://live.douyin.com/845632139263",
            proxy="http://127.0.0.1:7890",
        )
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")

    async def test_build_single_recording_payload_normalizes_raw_douyin_short_link(self):
        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(return_value="https://live.douyin.com/845632139263"),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            recordings_info = await self.dialog._build_single_recording_payload(
                url_value="https://v.douyin.com/fBjnc1ZLEEY/",
                streamer_name_value="主播",
                quality_value="OD",
                record_format_value="TS",
                recording_dir_value="",
                segment_visible=False,
                segment_time_value="1800",
                scheduled_recording_enabled=False,
                scheduled_start_time_values=["", ""],
                monitor_hours_values=["", ""],
                message_push_enabled=True,
                only_notify_no_record=False,
                flv_use_direct_download=False,
                rec_id=None,
                initial_values={},
            )

        self.assertEqual(recordings_info[0]["url"], "https://live.douyin.com/845632139263")
        normalize_mock.assert_awaited_once_with(
            "https://v.douyin.com/fBjnc1ZLEEY/",
            proxy="http://127.0.0.1:7890",
        )
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")

    async def test_build_single_recording_payload_normalizes_douyin_share_text(self):
        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(return_value="https://live.douyin.com/845632139263"),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            recordings_info = await self.dialog._build_single_recording_payload(
                url_value=(
                    "8- #在抖音，记录美好生活#【主播】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                    "https://v.douyin.com/fBjnc1ZLEEY/"
                ),
                streamer_name_value="主播",
                quality_value="OD",
                record_format_value="TS",
                recording_dir_value="/tmp/output",
                segment_visible=False,
                segment_time_value="1800",
                scheduled_recording_enabled=False,
                scheduled_start_time_values=["", ""],
                monitor_hours_values=["", ""],
                message_push_enabled=True,
                only_notify_no_record=False,
                flv_use_direct_download=False,
                rec_id=None,
                initial_values={},
            )

        self.assertEqual(recordings_info[0]["url"], "https://live.douyin.com/845632139263")
        normalize_mock.assert_awaited_once_with(
            (
                "8- #在抖音，记录美好生活#【主播】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/fBjnc1ZLEEY/"
            ),
            proxy="http://127.0.0.1:7890",
        )
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")

    async def test_build_single_recording_payload_skips_normalization_for_non_douyin_direct_url(self):
        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("虎牙直播", "huya"),
        ) as platform_mock:
            recordings_info = await self.dialog._build_single_recording_payload(
                url_value="https://www.huya.com/12345",
                streamer_name_value="主播",
                quality_value="OD",
                record_format_value="TS",
                recording_dir_value="",
                segment_visible=False,
                segment_time_value="1800",
                scheduled_recording_enabled=False,
                scheduled_start_time_values=["", ""],
                monitor_hours_values=["", ""],
                message_push_enabled=True,
                only_notify_no_record=False,
                flv_use_direct_download=False,
                rec_id=None,
                initial_values={},
            )

        self.assertEqual(recordings_info[0]["url"], "https://www.huya.com/12345")
        normalize_mock.assert_not_awaited()
        platform_mock.assert_called_once_with("https://www.huya.com/12345")

    async def test_single_input_share_text_submit_enables_confirm_and_saves(self):
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        single_input_controls = alert_dialog.content.tabs[0].content.content.controls
        url_field = single_input_controls[1]
        streamer_name_field = single_input_controls[2]
        confirm_button = alert_dialog.actions[1]

        self.assertTrue(confirm_button.disabled)

        url_field.value = (
            "8- #在抖音，记录美好生活#【主播】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
            "https://v.douyin.com/fBjnc1ZLEEY/"
        )
        streamer_name_field.value = "主播"

        await url_field.on_change(None)

        self.assertFalse(confirm_button.disabled)

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(return_value="https://live.douyin.com/845632139263"),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            await confirm_button.on_click(None)

        self.on_confirm_callback.assert_awaited_once()
        recordings_info = self.on_confirm_callback.await_args.args[0]
        self.assertEqual(recordings_info[0]["url"], "https://live.douyin.com/845632139263")
        self.assertFalse(alert_dialog.open)
        normalize_mock.assert_awaited_once_with(
            (
                "8- #在抖音，记录美好生活#【主播】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/fBjnc1ZLEEY/"
            ),
            proxy="http://127.0.0.1:7890",
        )
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")

    async def test_single_input_normalization_failure_keeps_dialog_open_and_shows_error(self):
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        single_input_controls = alert_dialog.content.tabs[0].content.content.controls
        url_field = single_input_controls[1]
        streamer_name_field = single_input_controls[2]

        url_field.value = "https://v.douyin.com/fBjnc1ZLEEY/"
        streamer_name_field.value = "主播"

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(side_effect=DouyinNormalizationError("bad input")),
        ), patch(
            "app.ui.components.business.recording_dialog.get_platform_info"
        ) as platform_mock:
            await alert_dialog.actions[1].on_click(None)

        self.on_confirm_callback.assert_not_awaited()
        platform_mock.assert_not_called()
        self.assertTrue(alert_dialog.open)
        self.assertEqual(
            self.app.snack_bar.messages,
            [("Failed to parse Douyin link", {"duration": 3000})],
        )

    async def test_single_input_duplicate_detection_normalizes_existing_saved_douyin_url(self):
        self.app.record_manager.recordings = [
            FakeRecording(
                "8- #在抖音，记录美好生活#【主播甲】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/existing123/"
            )
        ]
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        single_input_controls = alert_dialog.content.tabs[0].content.content.controls
        url_field = single_input_controls[1]
        streamer_name_field = single_input_controls[2]
        confirm_button = alert_dialog.actions[1]

        url_field.value = "https://v.douyin.com/new456/"
        streamer_name_field.value = "主播甲"

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(
                side_effect=[
                    "https://live.douyin.com/845632139263",
                    "https://live.douyin.com/845632139263",
                ]
            ),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            await confirm_button.on_click(None)

        self.on_confirm_callback.assert_not_awaited()
        self.assertEqual(normalize_mock.await_count, 2)
        self.assertEqual(platform_mock.call_count, 1)
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")
        self.assertTrue(alert_dialog.open)
        self.assertIs(self.app.page.overlay[-1], self.dialog.url_duplicate_confirm_dialog)


class RecordingDialogBatchInputTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = FakeApp()
        self.on_confirm_callback = AsyncMock()
        self.dialog = RecordingDialog(self.app, on_confirm_callback=self.on_confirm_callback)

    async def test_batch_input_normalizes_each_douyin_line_before_dedup(self):
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        tabs = alert_dialog.content
        batch_input = tabs.tabs[1].content.content
        confirm_button = alert_dialog.actions[1]

        tabs.selected_index = 1
        batch_input.value = "\n".join(
            [
                "0, https://v.douyin.com/first123/, 主播甲",
                (
                    "1，9- #在抖音，记录美好生活#【主播乙】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                    "https://v.douyin.com/second456/，主播乙"
                ),
            ]
        )

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(
                side_effect=[
                    "https://live.douyin.com/845632139263",
                    "https://live.douyin.com/845632139263",
                ]
            ),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            await confirm_button.on_click(None)

        self.on_confirm_callback.assert_awaited_once()
        recordings_info = self.on_confirm_callback.await_args.args[0]
        self.assertEqual(len(recordings_info), 1)
        self.assertEqual(recordings_info[0]["url"], "https://live.douyin.com/845632139263")
        self.assertEqual(recordings_info[0]["streamer_name"], "主播甲")
        self.assertEqual(
            normalize_mock.await_args_list[0].args,
            ("https://v.douyin.com/first123/",),
        )
        self.assertEqual(
            normalize_mock.await_args_list[1].args,
            (
                "9- #在抖音，记录美好生活#【主播乙】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/second456/",
            ),
        )
        for await_call in normalize_mock.await_args_list:
            self.assertEqual(await_call.kwargs, {"proxy": "http://127.0.0.1:7890"})
        self.assertEqual(platform_mock.call_count, 2)
        platform_mock.assert_called_with("https://live.douyin.com/845632139263")
        self.assertFalse(alert_dialog.open)

    async def test_batch_input_aborts_entire_submission_when_douyin_normalization_fails(self):
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        tabs = alert_dialog.content
        batch_input = tabs.tabs[1].content.content
        confirm_button = alert_dialog.actions[1]

        tabs.selected_index = 1
        batch_input.value = "\n".join(
            [
                "0, https://v.douyin.com/first123/, 主播甲",
                "https://v.douyin.com/broken456/, 主播乙",
            ]
        )

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(
                side_effect=[
                    "https://live.douyin.com/845632139263",
                    DouyinNormalizationError("bad input"),
                ]
            ),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            await confirm_button.on_click(None)

        self.on_confirm_callback.assert_not_awaited()
        self.assertEqual(normalize_mock.await_count, 2)
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")
        self.assertTrue(alert_dialog.open)
        self.assertEqual(
            self.app.snack_bar.messages,
            [("Failed to parse Douyin link", {"duration": 3000})],
        )

    async def test_batch_input_dedups_against_existing_saved_douyin_share_link_after_normalization(self):
        self.app.record_manager.recordings = [
            FakeRecording(
                "8- #在抖音，记录美好生活#【主播甲】正在直播，复制下方链接，打开【抖音】，直接观看直播！ "
                "https://v.douyin.com/existing123/"
            )
        ]
        await self.dialog.show_dialog()

        alert_dialog = self.app.page.overlay[-1]
        tabs = alert_dialog.content
        batch_input = tabs.tabs[1].content.content
        confirm_button = alert_dialog.actions[1]

        tabs.selected_index = 1
        batch_input.value = "0, https://v.douyin.com/new456/, 主播甲"

        with patch(
            "app.ui.components.business.recording_dialog.normalize_douyin_input",
            new=AsyncMock(
                side_effect=[
                    "https://live.douyin.com/845632139263",
                    "https://live.douyin.com/845632139263",
                ]
            ),
        ) as normalize_mock, patch(
            "app.ui.components.business.recording_dialog.get_platform_info",
            return_value=("抖音直播", "douyin"),
        ) as platform_mock:
            await confirm_button.on_click(None)

        self.on_confirm_callback.assert_awaited_once_with([])
        self.assertEqual(normalize_mock.await_count, 2)
        self.assertEqual(platform_mock.call_count, 1)
        platform_mock.assert_called_once_with("https://live.douyin.com/845632139263")
        self.assertFalse(alert_dialog.open)


if __name__ == "__main__":
    unittest.main()
