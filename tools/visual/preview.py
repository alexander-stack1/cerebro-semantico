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
import zlib

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


def validate_png(data):
    """Valida chunks/CRC e tamanho descomprimido do PNG RGB/RGBA 8 bits do Chromium."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('PNG inválido')
    offset, chunks, payload = 8, [], []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('PNG truncado')
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 8 + size
        if end + 4 > len(data):
            raise ValueError('PNG truncado')
        body = data[offset + 8:end]
        if zlib.crc32(kind + body) != struct.unpack('>I', data[end:end + 4])[0]:
            raise ValueError('CRC do PNG inválido')
        chunks.append(kind)
        if kind == b'IHDR':
            if chunks != [b'IHDR'] or len(body) != 13:
                raise ValueError('IHDR inválido')
            width, height, bits, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if (width, height, bits, compression, filtering, interlace) != (1440, 900, 8, 0, 0, 0) or color not in (2, 6):
                raise ValueError('PNG precisa ser RGB/RGBA 1440x900, 8 bits')
        if kind == b'IDAT':
            payload.append(body)
        offset = end + 4
        if kind == b'IEND':
            if body or offset != len(data):
                raise ValueError('IEND inválido')
            break
    if not chunks or chunks[0] != b'IHDR' or chunks[-1] != b'IEND' or not payload:
        raise ValueError('Estrutura PNG incompleta')
    row = 1440 * (3 if color == 2 else 4) + 1
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(b''.join(payload), row * 900 + 1)
    if len(pixels) != row * 900 or not decoder.eof or decoder.unused_data:
        raise ValueError('Dados PNG incompletos ou excedentes')
    if any(pixels[i] > 4 for i in range(0, len(pixels), row)):
        raise ValueError('Filtro PNG inválido')


def verify_ci(receipt):
    """Confere run concluído e igualdade byte a byte com o artefato servido pelo GitHub."""
    run = receipt['ci_run']
    repo = 'alexander-stack1/cerebro-semantico'
    if run is None:
        raise ValueError('A publicação exige captura gerada no CI.')
    info = json.loads(subprocess.check_output(['gh', 'api', 'repos/' + repo + '/actions/runs/' + run], text=True))
    if (info['status'], info['conclusion'], info['head_sha'], info['path']) != (
            'completed', 'success', receipt['head_revision'], '.github/workflows/ci.yml'):
        raise ValueError('Run de origem não confere')
    with tempfile.TemporaryDirectory(prefix='cerebro-origin-') as folder:
        subprocess.run(['gh', 'run', 'download', run, '--repo', repo, '--name',
                        'preview-' + receipt['revision'], '--dir', folder], check=True, capture_output=True)
        for name in ('preview.png', 'preview-origin.json'):
            if (Path(folder) / name).read_bytes() != (ROOT / 'docs/img' / name).read_bytes():
                raise ValueError('Artefato do CI difere do arquivo versionado')
    print('preview: run e artefato do GitHub conferidos')


def check(with_ci=False):
    check_example()
    receipt = json.loads(RECEIPT.read_text())
    for key in ('revision', 'head_revision'):
        if not re.fullmatch(r'[0-9a-f]{40}', receipt.get(key, '')):
            raise ValueError('Revisão de origem inválida')
    if 'ci_run' not in receipt or (receipt['ci_run'] is not None and not re.fullmatch(r'[0-9]+', receipt['ci_run'])):
        raise ValueError('Run de origem inválido')
    if receipt.get('command') != 'python3 tools/visual/preview.py' or not receipt.get('capture') or not receipt.get('dependencies'):
        raise ValueError('Metadados de origem incompletos')
    expected = {p: digest(p) for p in (*INPUTS, IMAGE)}
    if receipt['sha256'] != expected:
        raise ValueError('Preview ou origem mudou: regenere o preview.')
    validate_png((ROOT / IMAGE).read_bytes())
    if with_ci:
        verify_ci(receipt)
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
        'head_revision': os.environ.get('PREVIEW_HEAD_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
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
    ap.add_argument('--verify-ci', action='store_true', help='confere run e artefato remoto via gh')
    args = ap.parse_args()
    check(args.verify_ci) if args.check or args.verify_ci else generate()
