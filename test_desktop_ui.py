import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication, QPushButton
    import desktop_ui
except ImportError:  # optional during CLI-only installs
    QApplication = None
    desktop_ui = None

from app_config import AppConfig


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_launcher_builds_and_returns_edited_settings(self):
        class FakePreview:
            def __init__(self):
                self.started = None

            def start(self, index):
                self.started = index

            def stop(self):
                pass

            def snapshot(self):
                return None, None

        config = AppConfig()
        with patch.object(desktop_ui, "CameraPreview", FakePreview):
            launcher = desktop_ui.Launcher(config, lambda cfg: None)
            self.assertEqual(launcher.effects.count(), len(desktop_ui.EFFECTS))
            launcher.camera.setValue(3)
            launcher.goku_delay.setValue(0.25)
            launcher.effects.setCurrentRow(1)
            updated = launcher.current_config()
            self.assertEqual((updated.camera, updated.mode, updated.goku_delay),
                             (3, "naruto", 0.25))
            launcher.close()

    def test_goku_hides_the_gesture_only_vanish_button(self):
        class FakeEngine:
            def start(self): pass
            def stop(self): pass
            def join(self): pass
            def snapshot(self): return None, "", None, False
            def command(self, name): pass

        window = desktop_ui.PreviewWindow(FakeEngine(), lambda: None, mode="goku")
        buttons = {button.text(): button for button in window.findChildren(QPushButton)}
        self.assertFalse(buttons["Vanish"].isEnabled())
        self.assertTrue(buttons["Reappear"].isEnabled())
        window.close()

    def test_window_title_matches_obs_capture_contract(self):
        engine = None
        self.assertEqual(desktop_ui.WINDOW_TITLE, "Webcam Preview")


if __name__ == "__main__":
    unittest.main()
