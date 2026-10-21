"""Injeta o JSON do grafo na página 3D.

Uso:
  python3 pipeline/embed_viewer.py --template prototype/cerebro-semantico-3d.html --json grafo.json \\
      --out meu-cerebro.html [--out-bare meu-cerebro-sem-esqueleto.html]

--out       página completa, abre com duplo clique.
--out-bare  mesma página sem doctype, <html>, <head> e <body>, para hosts que injetam o
            esqueleto HTML sozinhos (por exemplo, publicação como Artifact no claude.ai).
"""
import argparse
import json
import re
import sys

MARK = 'const BRAIN_DATA = '


def embed(template, data):
    """Troca o valor de BRAIN_DATA no template. O JSON entra numa linha só, com </ escapado."""
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    i = template.index(MARK)
    j = template.index(';\n', i)
    return template[:i] + MARK + js + template[j:]


def strip_skeleton(page):
    """Remove o esqueleto HTML. Falha se o template mudou de forma inesperada."""
    title = re.search(r'<title>.*?</title>\n', page).group(0)
    head_comment = page[page.index('<!--'):page.index('-->') + 3]
    out = page
    parts = ['<!doctype html>\n', head_comment + '\n', '<html lang="pt-BR">\n<head>\n',
             '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n',
             title, '</head>\n<body>\n', '</body>\n</html>\n']
    for x in parts:
        if out.count(x) != 1:
            raise ValueError('template inesperado, trecho ausente ou repetido: ' + x[:40])
        out = out.replace(x, '')
    out = title + head_comment + '\n' + out
    if re.search(r'<(html|body|head)[\s>]', out):
        raise ValueError('sobrou esqueleto HTML na versão sem esqueleto')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--template', required=True)
    ap.add_argument('--json', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--out-bare', default=None)
    a = ap.parse_args(argv)
    with open(a.template, encoding='utf-8') as fh:
        tpl = fh.read()
    with open(a.json, encoding='utf-8') as fh:
        data = json.load(fh)
    page = embed(tpl, data)
    with open(a.out, 'w', encoding='utf-8') as fh:
        fh.write(page)
    msg = f"nós {len(data['nodes'])} | página {len(page) // 1024} KB"
    if a.out_bare:
        bare = strip_skeleton(page)
        with open(a.out_bare, 'w', encoding='utf-8') as fh:
            fh.write(bare)
        msg += f' | sem esqueleto {len(bare) // 1024} KB'
    print(msg)
    return 0


if __name__ == '__main__':
    sys.exit(main())
