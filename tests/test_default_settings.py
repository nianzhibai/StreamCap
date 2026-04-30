import json
import pathlib
import unittest


class DefaultSettingsTests(unittest.TestCase):
    def test_default_recording_format_is_mp4(self):
        settings = json.loads(pathlib.Path("config/default_settings.json").read_text(encoding="utf-8"))

        assert settings["video_format"] == "MP4"

    def test_proxy_is_disabled_by_default(self):
        settings = json.loads(pathlib.Path("config/default_settings.json").read_text(encoding="utf-8"))

        assert not settings["enable_proxy"]

    def test_recording_dialog_labels_describe_mp4_default(self):
        zh = json.loads(pathlib.Path("locales/zh_CN.json").read_text(encoding="utf-8"))
        en = json.loads(pathlib.Path("locales/en.json").read_text(encoding="utf-8"))

        assert "默认MP4" in zh["recording_dialog"]["select_record_format"]
        assert "Default mp4" in en["recording_dialog"]["select_record_format"]


if __name__ == "__main__":
    unittest.main()
