"""Prévia animada precisa corresponder ao MP4 e ao procedimento registrados."""
import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import _util
sys.path.insert(0, str(Path(_util.ROOT) / 'tools/visual'))
import animated_preview


class AnimatedPreviewTest(unittest.TestCase):
    def test_origem_versionada_confere(self):
        with contextlib.redirect_stdout(io.StringIO()):
            animated_preview.check()

    def test_gif_adulterado_bloqueia(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (*animated_preview.INPUTS, *animated_preview.OUTPUTS, animated_preview.RECEIPT):
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(animated_preview.ROOT / name, dest)
            target = root / animated_preview.OUTPUTS[0]
            target.write_bytes(target.read_bytes() + b'alterado')
            with patch.object(animated_preview, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'hashes'):
                    animated_preview.check()
