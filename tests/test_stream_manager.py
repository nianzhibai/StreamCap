import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from app.core.recording.stream_manager import LiveStreamRecorder
from app.models.recording.recording_model import Recording
from app.models.recording.recording_status_model import RecordingStatus


class FakePubSub:
    def send_others_on_topic(self, *_args, **_kwargs):
        return None


class FakePage:
    def __init__(self):
        self.pubsub = FakePubSub()

    def run_task(self, *_args, **_kwargs):
        return None


class FakeLanguageManager:
    def __init__(self):
        self.language = {
            "recording_manager": {
                "recorded": "Recorded",
                "monitor_stopped": "Stopped",
                "segment_limit_reached": "Segment limit reached",
                "SEGMENT_LIMIT_REACHED": "Segment limit reached",
            },
            "stream_manager": {
                "record_stream_error": "record error",
                "no_ffmpeg_tip": "no ffmpeg",
            },
        }

    def add_observer(self, *_args, **_kwargs):
        return None


class FakeSettings:
    def __init__(self, output_dir):
        self.user_config = {
            "convert_to_mp4": False,
            "delete_original": False,
            "execute_custom_script": False,
            "default_platform_with_proxy": "",
        }
        self.accounts_config = {}
        self.cookies_config = {}
        self.output_dir = output_dir

    def get_video_save_path(self):
        return self.output_dir


class FakeRecordManager:
    def __init__(self):
        self.active_recorders = {}
        self.stop_monitor_calls = []
        self.check_if_live = object()

    async def stop_monitor_recording(self, recording, auto_save=True):
        self.stop_monitor_calls.append((recording, auto_save))
        recording.monitor_status = False
        recording.status_info = RecordingStatus.STOPPED_MONITORING

    async def persist_recordings(self):
        return None


class FakeRecordCardManager:
    async def update_card(self, *_args, **_kwargs):
        return None


class FakeSnackBar:
    async def show_snack_bar(self, *_args, **_kwargs):
        return None


class FakeApp:
    def __init__(self, output_dir):
        self.settings = FakeSettings(output_dir)
        self.language_manager = FakeLanguageManager()
        self.page = FakePage()
        self.record_manager = FakeRecordManager()
        self.record_card_manager = FakeRecordCardManager()
        self.snack_bar = FakeSnackBar()
        self.subprocess_start_up_info = None
        self.recording_enabled = True
        self.added_processes = []

    def add_ffmpeg_process(self, process):
        self.added_processes.append(process)


class FakeProcess:
    def __init__(self):
        self.returncode = 0
        self.stdin = None

    async def communicate(self):
        return b"", b""


def make_recording():
    recording = Recording(
        rec_id="rec-1",
        url="https://example.com/live",
        streamer_name="streamer",
        record_format="MP4",
        quality="OD",
        segment_record=True,
        segment_time="1800",
        segment_count=2,
        monitor_status=True,
        scheduled_recording=False,
        scheduled_start_time="",
        monitor_hours="",
        recording_dir=None,
        enabled_message_push=False,
        only_notify_no_record=False,
        flv_use_direct_download=False,
    )
    recording.is_live = True
    recording.is_recording = True
    recording.status_info = RecordingStatus.RECORDING
    return recording


class LiveStreamRecorderSegmentLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_monitor_segment_count_marks_segment_limit_reached(self):
        with tempfile.TemporaryDirectory() as output_dir:
            recording = make_recording()
            app = FakeApp(output_dir)
            recorder = LiveStreamRecorder(
                app,
                recording,
                {
                    "platform_key": "douyin",
                    "platform": "Douyin",
                    "live_url": recording.url,
                    "output_dir": output_dir,
                    "segment_record": True,
                    "segment_count": 2,
                    "save_format": "mp4",
                },
            )

            with (
                patch("app.core.recording.stream_manager.asyncio.sleep", new=AsyncMock()),
                patch("glob.glob", return_value=["part_000.mp4", "part_001.mp4"]),
            ):
                await recorder.monitor_segment_count(f"{output_dir}/part_%03d.mp4")

        assert recorder.should_stop
        assert recording.status_info == RecordingStatus.SEGMENT_LIMIT_REACHED
        assert not recording.monitor_status
        assert len(app.record_manager.stop_monitor_calls) == 1

    async def test_start_ffmpeg_preserves_segment_limit_status_after_process_exit(self):
        with tempfile.TemporaryDirectory() as output_dir:
            recording = make_recording()
            app = FakeApp(output_dir)
            recorder = LiveStreamRecorder(
                app,
                recording,
                {
                    "platform_key": "douyin",
                    "platform": "Douyin",
                    "live_url": recording.url,
                    "output_dir": output_dir,
                    "segment_record": True,
                    "segment_count": 2,
                    "save_format": "mp4",
                },
            )
            recorder.segment_limit_reached = True

            with patch("app.core.recording.stream_manager.asyncio.create_subprocess_exec", return_value=FakeProcess()):
                await recorder.start_ffmpeg(
                    record_name="streamer",
                    live_url=recording.url,
                    record_url="https://example.com/stream.m3u8",
                    ffmpeg_command=["ffmpeg", "-i", "input", f"{output_dir}/part_%03d.mp4"],
                    save_type="mp4",
                )

        assert recording.status_info == RecordingStatus.SEGMENT_LIMIT_REACHED
        assert not recording.monitor_status


if __name__ == "__main__":
    unittest.main()
