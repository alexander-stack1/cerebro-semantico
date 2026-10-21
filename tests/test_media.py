"""As demonstrações devem falhar se a mídia ou sua origem mudar."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import _util
sys.path.insert(0, str(Path(_util.ROOT) / 'tools/visual'))
import demo_media


class MediaOriginTest(unittest.TestCase):
    def test_arquivo_adulterado_bloqueia(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (*demo_media.INPUTS, *demo_media.OUTPUTS):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'original')
            receipt = {'head_revision': 'a' * 40, 'revision': 'b' * 40, 'ci_run': '123',
                       'sha256': {p: hashlib.sha256(b'original').hexdigest()
                                  for p in (*demo_media.INPUTS, *demo_media.OUTPUTS)}}
            (root / demo_media.RECEIPT).write_text(json.dumps(receipt))
            with patch.object(demo_media, 'ROOT', root):
                for target in ('docs/media/navegacao.mp4', 'prototype/cerebro-semantico-3d.html'):
                    (root / target).write_bytes(b'alterado')
                    with self.assertRaisesRegex(ValueError, 'hashes'):
                        demo_media.check()
                    (root / target).write_bytes(b'original')

    def test_manifest_incompleto_bloqueia(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / demo_media.RECEIPT
            path.parent.mkdir(parents=True)
            path.write_text('{}')
            with patch.object(demo_media, 'ROOT', root):
                with self.assertRaises(ValueError):
                    demo_media.check()
