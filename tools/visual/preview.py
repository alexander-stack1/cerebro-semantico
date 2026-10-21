"""Gera o preview do exemplo pelo smoke e registra hashes de origem.

Uso: python3 tools/visual/preview.py [--check]
Geração requer as dependências opcionais do smoke. --check usa só biblioteca padrão.
A animação varia entre capturas; reproduz-se o procedimento, não os pixels.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'docs/img/preview.png'
RECEIPT = ROOT / 'docs/img/preview-origin.json'
INPUTS = ('examples/gerar_vault_exemplo.py', 'examples/sample_graph.json',
          'config/config.example.json', 'pipeline/build_graph.py', 'pipeline/vault.py',
          'pipeline/config.py', 'pipeline/embed_viewer.py',
          'prototype/cerebro-semantico-3d.html', 'tools/visual/smoke.py',
          'tools/visual/measure.py', 'tools/visual/preview.py', '.github/workflows/ci.yml')


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def check_example():
    html = (ROOT / 'prototype/cerebro-semantico-3d.html').read_text()
    match = re.search(r'const BRAIN_DATA = (.*);\n', html)
    graph = json.loads((ROOT / 'examples/sample_graph.json').read_text())
    if not match or json.loads(match.group(1).replace('<\\/', '</')) != graph:
        raise ValueError('O HTML não contém o grafo de exemplo.')


def check():
    check_example()
    receipt = json.loads(RECEIPT.read_text())
    expected = {p: digest(p) for p in (*INPUTS, IMAGE)}
    if receipt['sha256'] != expected:
        raise ValueError('Preview ou origem mudou: regenere o preview.')
    image = (ROOT / IMAGE).read_bytes()
    if image[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', image[16:24]) != (1440, 900):
        raise ValueError('Preview precisa ser PNG 1440x900.')
    print('preview: hashes e grafo de exemplo OK')


def generate():
    check_example()
    # Prova gerador -> vault -> grafo; falha antes de capturar se divergirem.
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                    '-p', 'test_build_graph.py'], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix='cerebro-preview-') as folder:
        command = [sys.executable, 'tools/visual/smoke.py', '--html',
                   'prototype/cerebro-semantico-3d.html', '--out', folder,
                   '--width', '1440', '--height', '900', '--wait', '14',
                   '--node', 'Reforma do banheiro']
        subprocess.run(command, cwd=ROOT, check=True)
        shutil.copyfile(Path(folder) / 'visao-geral.png', ROOT / IMAGE)
    receipt = {
        'command': 'python3 tools/visual/preview.py',
        'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'ci_run': os.environ.get('GITHUB_RUN_ID'),
        'capture': 'Chromium / SwiftShader; smoke; viewport 1440x900; wait 14s; overview',
        'dependencies': {name: version(name) for name in ('playwright', 'pillow', 'numpy')},
        'sha256': {p: digest(p) for p in (*INPUTS, IMAGE)},
    }
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    check()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    check() if args.check else generate()
