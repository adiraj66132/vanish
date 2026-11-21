import unittest
from unittest.mock import patch

import camera_engine as engine_module
from camera_engine import CameraEngine


class EngineTests(unittest.TestCase):
    def test_pipeline_hooks_receive_frames_status_and_commands(self):
        seen = {}

        def fake_run(args, resources, mode, session, **hooks):
            hooks["on_status"]("Capturing background")
            hooks["on_frame"]("frame")
            seen["command"] = hooks["poll_command"]()
            seen["on_frame"] = hooks["on_frame"]
            self.assertIsNone(hooks["on_fullscreen"](True))

        with patch.object(engine_module, "run_camera", side_effect=fake_run):
            engine = CameraEngine(object(), "normal")
            engine.command("recapture")
            engine.start()
            engine.join(timeout=2)

        self.assertEqual(seen["command"], "recapture")
        frame, status, error, finished = engine.snapshot()
        self.assertEqual((frame, status, error, finished),
                         ("frame", "Capturing background", None, True))

    def test_errors_are_captured_instead_of_crashing_the_thread(self):
        with patch.object(engine_module, "run_camera", side_effect=RuntimeError("camera lost")):
            engine = CameraEngine(object(), "normal")
            engine.start()
            engine.join(timeout=2)
        self.assertIsInstance(engine.snapshot()[2], RuntimeError)
        self.assertTrue(engine.snapshot()[3])

    def test_unknown_commands_are_ignored(self):
        engine = CameraEngine(object(), "normal")
        engine.command("explode")
        self.assertIsNone(engine._poll_command())


if __name__ == "__main__":
    unittest.main()
