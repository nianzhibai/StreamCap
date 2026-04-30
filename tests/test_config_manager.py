import json
import pathlib
import tempfile
import unittest

from app.core.config.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_existing_user_config_migrates_legacy_recording_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / "config"
            config_dir.mkdir()
            (config_dir / "default_settings.json").write_text(
                json.dumps({"video_format": "MP4", "enable_proxy": False}),
                encoding="utf-8",
            )
            (config_dir / "user_settings.json").write_text(
                json.dumps({"video_format": "TS", "enable_proxy": True}),
                encoding="utf-8",
            )

            manager = ConfigManager(temp_dir)

            user_config = manager.load_user_config()
            persisted_config = json.loads((config_dir / "user_settings.json").read_text(encoding="utf-8"))

        assert user_config["video_format"] == "MP4"
        assert not user_config["enable_proxy"]
        assert persisted_config["video_format"] == "MP4"
        assert not persisted_config["enable_proxy"]

    def test_user_config_migration_does_not_reapply_after_marker_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / "config"
            config_dir.mkdir()
            (config_dir / "default_settings.json").write_text(
                json.dumps({"video_format": "MP4", "enable_proxy": False}),
                encoding="utf-8",
            )
            (config_dir / "user_settings.json").write_text(
                json.dumps(
                    {
                        "video_format": "TS",
                        "enable_proxy": True,
                        "_config_migrations": ["2026-04-30-default-mp4-proxy-off"],
                    }
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(temp_dir)

            user_config = manager.load_user_config()

        assert user_config["video_format"] == "TS"
        assert user_config["enable_proxy"]


if __name__ == "__main__":
    unittest.main()
