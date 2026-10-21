"""Auditoria do vault: sigilo, estilo e links quebrados.

Uso:
  python3 pipeline/lint_vault.py --config config/config.json [--vault DIR]

Sai com código 1 se achar dado sigiloso: CPF, processo, telefone, e-mail, credencial,
ou nome de contato sigiloso (nomes do arquivo private.aliases e de private.sensitive_names).
Estilo (travessão, frases proibidas) e links quebrados só geram aviso.
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from redact import detect  # noqa: E402
from vault import WIKILINK, fold  # noqa: E402


def sensitive_names(cfg):
    """Nomes que nunca podem aparecer numa nota. Ignora nomes curtos e números de telefone."""
    lc, p = cfg['lint'], cfg['private']
    names = set()
    if p['aliases'] and os.path.exists(p['aliases']):
        with open(p['aliases'], encoding='utf-8') as fh:
            for v in json.load(fh).values():
                n = v.get('name', '')
                if not re.search(r'\d{4,}', n) and len(n) >= lc['sensitive_name_min_len']:
                    names.add(fold(n))
    if p['sensitive_names'] and os.path.exists(p['sensitive_names']):
        with open(p['sensitive_names'], encoding='utf-8') as fh:
            names |= {fold(x.strip()) for x in fh if x.strip() and not x.startswith('#')}
    return names


def lint(vault, cfg):
    lc = cfg['lint']
    names = sensitive_names(cfg)
    exempt = re.compile(lc['phrase_exempt_files_regex']) if lc['phrase_exempt_files_regex'] else None
    files = sorted(os.path.join(d, f) for d, _, fs in os.walk(vault) for f in fs if f.endswith('.md'))
    titles = {os.path.basename(f)[:-3] for f in files}
    issues = collections.defaultdict(list)
    broken = collections.defaultdict(set)
    critical = 0
    for f in files:
        with open(f, encoding='utf-8') as fh:
            t = fh.read()
        b = os.path.basename(f)
        nt = fold(t)
        if lc['flag_dashes'] and ('\u2014' in t or '\u2013' in t):
            issues['travessão'].append(b)
        for p in lc['forbidden_phrases']:
            if p in t.lower() and not (exempt and exempt.search(b)):
                issues['frase IA:' + p].append(b)
        for k in detect(t):
            issues['SIGILO ' + k].append(b)
            critical += 1
        for n in names:
            if n in nt:
                issues['SIGILO nome de contato sigiloso'].append(b)
                critical += 1
        for link in set(x.strip() for x in WIKILINK.findall(t)):
            if link not in titles:
                broken[link].add(b)
    return files, issues, broken, critical


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--config', required=True)
    ap.add_argument('--vault', help='sobrepõe vault.path do config')
    a = ap.parse_args(argv)
    cfg = cfgmod.load(a.config)
    vault = os.path.abspath(a.vault) if a.vault else cfg['vault']['path']
    if not vault:
        ap.error('informe --vault ou vault.path no config')
    files, issues, broken, critical = lint(vault, cfg)
    print('notas', len(files))
    for k, v in issues.items():
        print('ISSUE', k, len(v), sorted(set(v))[:10])
    print('links quebrados:', len(broken))
    for link, b in sorted(broken.items(), key=lambda kv: -len(kv[1]))[:30]:
        print(' ', len(b), '[[' + link + ']]', sorted(b)[:3])
    return 1 if critical else 0


if __name__ == '__main__':
    sys.exit(main())
