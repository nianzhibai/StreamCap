import pathlib
import unittest


class StartDebianScriptTests(unittest.TestCase):
    def test_script_contains_required_bootstrap_steps(self):
        script_path = pathlib.Path("start_debian.sh")

        self.assertTrue(script_path.exists(), "start_debian.sh should exist")

        content = script_path.read_text(encoding="utf-8")
        self.assertIn("python3", content)
        self.assertIn("python3-venv", content)
        self.assertIn("ffmpeg", content)
        self.assertIn(".env.example", content)
        self.assertIn("python3 main.py", content)

    def test_script_rebuilds_broken_virtualenv_instead_of_trusting_directory(self):
        content = pathlib.Path("start_debian.sh").read_text(encoding="utf-8")

        self.assertIn('VENV_ACTIVATE="${VENV_DIR}/bin/activate"', content)
        self.assertIn('python3 -m venv --clear "${VENV_DIR}"', content)

    def test_script_skips_reinstall_when_dependency_state_matches(self):
        content = pathlib.Path("start_debian.sh").read_text(encoding="utf-8")

        self.assertNotIn("python3 -m pip install --upgrade pip", content)
        self.assertIn("python3 -m pip check", content)
        self.assertIn('requirements.txt.sha256', content)
        self.assertIn('requirements-web.txt.sha256', content)


if __name__ == "__main__":
    unittest.main()
