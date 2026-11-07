import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from vanish_sound import VanishSound


class VanishSoundTests(unittest.TestCase):
    def _sample(self, directory):
        path = Path(directory) / "sample.MP3"
        path.write_bytes(b"audio-data")
        return path

    def test_falls_back_to_ffplay_when_pygame_mixer_is_unavailable(self):
        with TemporaryDirectory() as directory:
            with patch("vanish_sound.importlib.util.find_spec", return_value=None), \
                 patch("vanish_sound.shutil.which", return_value="/usr/bin/ffplay"):
                sound = VanishSound(self._sample(directory))
        self.assertEqual(sound.ffplay, "/usr/bin/ffplay")
        self.assertFalse(hasattr(sound, "sound"))

    def test_raises_without_mixer_or_ffplay(self):
        with TemporaryDirectory() as directory:
            with patch("vanish_sound.importlib.util.find_spec", return_value=None), \
                 patch("vanish_sound.shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "ffplay"):
                    VanishSound(self._sample(directory))

    def test_uses_pygame_mixer_when_available(self):
        mixer = SimpleNamespace(init=lambda **kwargs: None, get_init=lambda: None,
                               Sound=lambda path: object(), quit=lambda: None)
        with TemporaryDirectory() as directory:
            with patch("vanish_sound.importlib.util.find_spec", return_value=object()), \
                 patch.dict("sys.modules", {"pygame": SimpleNamespace(mixer=mixer)}):
                sound = VanishSound(self._sample(directory))
        self.assertTrue(hasattr(sound, "sound"))


if __name__ == "__main__":
    unittest.main()
