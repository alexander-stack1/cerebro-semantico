"""Utilidades comuns dos testes. Só biblioteca padrão."""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPE = os.path.join(ROOT, 'pipeline')
EXAMPLES = os.path.join(ROOT, 'examples')
CONFIG = os.path.join(ROOT, 'config', 'config.example.json')
sys.path.insert(0, PIPE)

import config as cfgmod  # noqa: E402


def load_example(**overrides):
    return cfgmod.load(CONFIG, overrides or None)


class TempDir:
    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix='cerebro-test-')
        return self.path

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)


def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)


def write_config(folder, extra):
    """Grava um config baseado no exemplo, com seções trocadas por extra, e devolve o caminho."""
    with open(CONFIG, encoding='utf-8') as fh:
        raw = json.load(fh)
    raw['vault']['path'] = os.path.join(EXAMPLES, 'vault')
    for k, v in extra.items():
        raw[k] = v
    path = os.path.join(folder, 'config.json')
    write_json(path, raw)
    return path
