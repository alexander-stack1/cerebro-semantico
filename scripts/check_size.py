"""Falha se um arquivo de texto versionado passar de 20.000 bytes (cerca de 5.000 tokens).

Uso: python3 scripts/check_size.py [--limit 20000]

Espelha a regra do hook pre-commit de tamanho: binários e assets ficam fora, e exceções
justificadas ficam em .agent-size-ignore (um glob por linha, "pasta/" vale para a pasta toda,
comentário depois de #). Roda no CI para quem não tem o hook instalado.
"""
import argparse
import fnmatch
import os
import subprocess
import sys

BINARY_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.svg', '.pdf', '.zip', '.gz', '.woff',
              '.woff2', '.ttf', '.otf', '.mp3', '.mp4', '.mov', '.webm', '.wav', '.ogg', '.sqlite', '.db'}


def ignore_patterns(root):
    path = os.path.join(root, '.agent-size-ignore')
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            p = line.split('#', 1)[0].strip()
            if p:
                out.append(p)
    return out


def ignored(f, patterns):
    if os.path.splitext(f)[1].lower() in BINARY_EXT:
        return True
    for p in patterns:
        if p.endswith('/') and f.startswith(p):
            return True
        if fnmatch.fnmatchcase(f, p):
            return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--limit', type=int, default=20000)
    a = ap.parse_args(argv)
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=True).stdout.strip()
    # -z: caminhos crus, sem as aspas e escapes que o git usa para nomes com acento
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, text=True, check=True).stdout.split('\0')
    pats = ignore_patterns(root)
    bad = []
    for f in filter(None, files):
        if ignored(f, pats):
            continue
        size = os.path.getsize(os.path.join(root, f))
        if size > a.limit:
            bad.append((size, f))
    for size, f in sorted(bad, reverse=True):
        print(f'{f}: {size} bytes (limite {a.limit})')
    if bad:
        print('Divida o arquivo por responsabilidade ou registre a exceção em .agent-size-ignore com justificativa.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
