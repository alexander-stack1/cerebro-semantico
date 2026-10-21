"""Leitura de um vault Markdown no formato Obsidian.

Cada nota é um arquivo .md. O título é o nome do arquivo sem extensão.
O frontmatter é lido como pares simples "chave: valor" (sem YAML completo).
Wikilinks são [[Título]], [[Título|apelido]] ou [[Título#seção]].
Linhas datadas começam com "- AAAA-MM-DD".
Linhas de evento ficam em notas cujo nome começa com o prefixo de eventos e seguem
o formato "- AAAA-MM-DD | Domínio | evento | [[Nota]]".
"""
import os
import re
import unicodedata

FRONTMATTER = re.compile(r'---\n(.*?)\n---\n', re.S)
WIKILINK = re.compile(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]')
LINK_TARGET = re.compile(r'\[\[([^\]|#]+)')
DATED_LINE = re.compile(r'^- (\d{4}-\d{2}-\d{2})', re.M)
# usada pelo construtor do grafo: só precisa da data e dos links no fim da linha
EVENT_LINE = re.compile(r'^- (\d{4}-\d{2}-\d{2})\s*\|.*\|\s*(\[\[.*\]\])\s*$')
# usada pela linha do tempo: data, domínio, texto do evento e links
EVENT_FIELDS = re.compile(r'^- (\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*(\[\[.*\]\])\s*$')


def fold(s):
    """Minúsculas e sem acento, para comparação tolerante."""
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def parse_frontmatter(text):
    m = FRONTMATTER.match(text)
    fm = {}
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
    return fm


def parse_tags(raw):
    return set(x.strip().lower() for x in re.sub(r'[\[\]]', '', raw or '').split(',') if x.strip())


def wikilinks(text):
    return set(x.strip() for x in WIKILINK.findall(text))


def iter_markdown(vault, ignore_files=()):
    """Percorre o vault em ordem estável. Devolve (pasta, arquivo, texto)."""
    ignore = set(ignore_files)
    for d, dirs, files in os.walk(vault):
        dirs.sort()
        for f in sorted(files):
            if not f.endswith('.md') or f in ignore:
                continue
            with open(os.path.join(d, f), encoding='utf-8') as fh:
                yield d, f, fh.read()


def read_notes(vault, ignore_files=(), events_prefix='Eventos'):
    """Lê todas as notas e as linhas de evento.

    Devolve (notes, events):
      notes  = {título: {title, folder, fm, tipo, conf, tags, links, dates}}
      events = [(AAAA-MM-DD, [títulos ligados])]
    """
    notes, events = {}, []
    for d, f, text in iter_markdown(vault, ignore_files):
        fm = parse_frontmatter(text)
        title = f[:-3]
        notes[title] = dict(
            title=title, folder=os.path.basename(d), fm=fm,
            tipo=fm.get('tipo', ''), conf=fm.get('confianca', ''),
            tags=parse_tags(fm.get('tags', '')), links=wikilinks(text),
            dates=DATED_LINE.findall(text))
        if events_prefix and f.startswith(events_prefix):
            for line in text.split('\n'):
                m = EVENT_LINE.match(line.strip())
                if m:
                    events.append((m.group(1), [x.strip() for x in LINK_TARGET.findall(m.group(2))]))
    return notes, events


def read_event_rows(vault, ignore_files=(), events_prefix='Eventos'):
    """Linhas de evento completas para a linha do tempo: {(data, domínio, texto, links, pasta)}."""
    rows = set()
    for d, f, text in iter_markdown(vault, ignore_files):
        if not f.startswith(events_prefix):
            continue
        for line in text.split('\n'):
            m = EVENT_FIELDS.match(line.strip())
            if m:
                rows.add((m.group(1), m.group(2).strip(), m.group(3), m.group(4), os.path.basename(d)))
    return rows
