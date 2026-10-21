"""A captura versionada precisa continuar vinculada às fontes verificadas."""
import contextlib
import io
import json
import struct
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import _util
sys.path.insert(0, str(Path(_util.ROOT) / 'tools/visual'))
import preview


class PreviewOriginTest(unittest.TestCase):
    def test_preview_versionado_confere(self):
        with contextlib.redirect_stdout(io.StringIO()):
            preview.check()

    def check_tampering(self, relative):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (*preview.INPUTS, preview.IMAGE, 'docs/img/preview-origin.json'):
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(preview.ROOT / name, destination)
            path = root / relative
            path.write_bytes(path.read_bytes() + b'\n')
            with patch.object(preview, 'ROOT', root), patch.object(preview, 'RECEIPT', root / 'docs/img/preview-origin.json'):
                with self.assertRaisesRegex(ValueError, 'origem mudou'):
                    preview.check()

    def test_imagem_alterada_falha(self):
        self.check_tampering(preview.IMAGE)

    def test_fonte_alterada_falha(self):
        self.check_tampering('prototype/cerebro-semantico-3d.html')

    def test_receipt_sem_origem_falha(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / 'receipt.json'
            receipt.write_text(json.dumps({'sha256': {}}))
            with patch.object(preview, 'RECEIPT', receipt):
                with self.assertRaisesRegex(ValueError, 'origem inválida'):
                    preview.check()

    def test_png_truncado_com_dimensoes_corretas_falha(self):
        data = b'\x89PNG\r\n\x1a\n' + b'\0' * 8 + struct.pack('>II', 1440, 900)
        with self.assertRaises(ValueError):
            preview.validate_png(data)

    def test_run_de_outra_revisao_falha(self):
        receipt = {'ci_run': '123', 'head_revision': 'a' * 40}
        info = {'status': 'completed', 'conclusion': 'success', 'head_sha': 'b' * 40,
                'path': '.github/workflows/ci.yml'}
        with patch.object(preview.subprocess, 'check_output', return_value=json.dumps(info)):
            with self.assertRaisesRegex(ValueError, 'Run de origem não confere'):
                preview.verify_ci(receipt)
