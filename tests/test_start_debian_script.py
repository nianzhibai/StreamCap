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


if __name__ == "__main__":
    unittest.main()
