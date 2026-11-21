import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app_config as cfg


class ConfigTests(unittest.TestCase):
    def test_defaults_round_trip_and_corrupt_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            with patch.object(cfg, "settings_path", return_value=path):
                config = cfg.AppConfig.load()
                self.assertEqual((config.fps, config.virtual_camera, config.mirror,
                                  config.goku_delay), (30.0, "auto", True, 3.0))
                config.mode, config.camera, config.goku_delay = "goku", 2, 0.5
                config.save()
                loaded = cfg.AppConfig.load()
                self.assertEqual((loaded.mode, loaded.camera, loaded.goku_delay),
                                 ("goku", 2, 0.5))
                path.write_text("{bad json", encoding="utf-8")
                self.assertEqual(cfg.AppConfig.load().mode, None)

    def test_bad_values_fall_back_but_unknown_keys_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text('{"fps": -1, "virtual_camera": "maybe", "extra": 3}',
                            encoding="utf-8")
            with patch.object(cfg, "settings_path", return_value=path):
                config = cfg.AppConfig.load()
                self.assertEqual(config.fps, 30.0)
                self.assertEqual(config.virtual_camera, "auto")
                self.assertFalse(hasattr(config, "extra"))

    def test_args_mapping(self):
        config = cfg.AppConfig(mode="goku", camera=1, mirror=False,
                               virtual_camera="off", goku_delay=0.25)
        args = config.to_args()
        self.assertEqual((args.mode, args.camera, args.no_mirror,
                          args.virtual_camera, args.goku_delay),
                         ("goku", 1, True, False, 0.25))

    def test_model_path_prefers_bundled_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "models").mkdir()
            (root / "models" / "gesture_recognizer.task").write_bytes(b"x")
            with patch.object(sys, "_MEIPASS", str(root), create=True), \
                 patch.object(cfg, "model_dir", return_value=root / "user"):
                self.assertEqual(cfg.model_path("gesture_recognizer.task"),
                                 root / "models" / "gesture_recognizer.task")
                self.assertEqual(cfg.model_path("other.task"), root / "user" / "other.task")


if __name__ == "__main__":
    unittest.main()
