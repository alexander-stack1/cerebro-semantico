"""Gera o JSON do grafo 3D a partir de um vault. Só temas: pessoas ficam de fora.

Uso:
  python3 pipeline/build_graph.py --config config/config.json --out grafo.json \\
      --source "Minhas notas · 13/07 a 18/10/2026" [--vault DIR] [--until AAAA-MM-DD] [--start AAAA-MM-DD]

Regras:
  peso         = grau do nó no grafo de links, normalizado (0.3 a 1.0)
  proximidade  = 0.45 base, +0.2 se o link é recíproco, +até 0.35 por vizinhança comum (Jaccard),
                 +0.05 se as notas estão na mesma pasta; faixa 0.36 a 1.0
  latentes     = pares sem link direto que dividem uma nota excluída (pessoa) ou 2+ tags;
                 no máximo graph.max_latent_per_node por nó; faixa 0.14 a 0.33
  atividade    = registros datados por semana: linhas "- AAAA-MM-DD" da nota e eventos que apontam para ela

Sai com código 1 se um nome de pessoa (título de nota do tipo pessoa) aparecer no JSON.
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from vault import fold, read_notes  # noqa: E402


def category_of(note, vcfg):
    """Categoria da nota: título explícito, depois regra por campo da pasta, depois mapa de pastas."""
    if note['title'] in vcfg['title_category']:
        return vcfg['title_category'][note['title']]
    rule = vcfg['folder_by_field'].get(note['folder'])
    if rule:
        return rule['map'].get(note['fm'].get(rule['field'], ''), rule.get('default'))
    return vcfg['folders'].get(note['folder'])


def build(cfg, source, until=None, start=None, today=None):
    v, gc = cfg['vault'], cfg['graph']
    notes, events = read_notes(v['path'], v['ignore_files'], v['events_prefix'])
    cats = cfg['categories']
    excl_types, excl_titles = set(v['exclude_types']), set(v['exclude_titles'])
    prefixes = tuple(v['exclude_title_prefixes'])
    keep = {t: n for t, n in notes.items()
            if n['tipo'] not in excl_types and t not in excl_titles
            and not (prefixes and t.startswith(prefixes)) and category_of(n, v)}
    excluded = set(notes) - set(keep)

    # grafo não dirigido entre todas as notas (as excluídas servem para as latentes)
    adj = collections.defaultdict(set)
    dirpair = collections.Counter()
    for t, n in notes.items():
        for link in n['links']:
            if link in notes and link != t:
                adj[t].add(link)
                adj[link].add(t)
                dirpair[(t, link)] += 1

    def nb(t):
        return {x for x in adj[t] if x in keep}

    edges = {}
    for a in keep:
        for b in nb(a):
            if a < b:
                na, nb_ = nb(a), nb(b)
                jac = len(na & nb_) / max(1, len(na | nb_))
                bidir = dirpair[(a, b)] > 0 and dirpair[(b, a)] > 0
                prox = 0.45 + (0.2 if bidir else 0) + 0.35 * min(1, jac * 2.2)
                if notes[a]['folder'] == notes[b]['folder']:
                    prox += 0.05
                edges[(a, b)] = round(min(1, max(0.36, prox)), 2)

    # latentes: vizinhos comuns numa nota excluída, ou 2+ tags em comum
    lat = collections.defaultdict(float)
    skip_types, skip_pref = set(v['latent_skip_types']), tuple(v['latent_skip_prefixes'])
    for x in sorted(excluded):
        if notes[x]['tipo'] in skip_types or (skip_pref and x.startswith(skip_pref)):
            continue
        ks = sorted(y for y in adj[x] if y in keep)
        if len(ks) > gc['latent_max_shared']:
            continue  # nota genérica demais
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                lat[(ks[i], ks[j])] += 1.0 / len(ks) ** 0.5
    stop = set(v['stop_tags'])
    kl = sorted(keep)
    for i in range(len(kl)):
        for j in range(i + 1, len(kl)):
            a, b = sorted((kl[i], kl[j]))
            shared = (keep[a]['tags'] & keep[b]['tags']) - stop
            if len(shared) >= 2:
                lat[(a, b)] += 0.35 * len(shared)
    cand = sorted(((round(val, 6), k) for k, val in lat.items() if k not in edges), reverse=True)
    per, latent = collections.Counter(), {}
    cap = gc['max_latent_per_node']
    for val, (a, b) in cand:
        if per[a] >= cap or per[b] >= cap:
            continue
        latent[(a, b)] = round(min(0.33, 0.14 + 0.06 * val), 2)
        per[a] += 1
        per[b] += 1

    deg = collections.Counter()
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    mx = max(deg.values()) if deg else 1

    people = [t for t, n in notes.items() if n['tipo'] == v['person_type']]
    owner = set(gc['owner_names'])
    rename = gc['rename']

    def clean_title(t):
        if t in rename:
            return rename[t]
        x = t
        for p in sorted(people, key=len, reverse=True):
            if p in owner:
                continue
            x = re.sub(r'\s*(com|do|da|de|e)?\s*(a|o|os|as)?\s*' + re.escape(p) + r'\b', '', x)
        return re.sub(r'\s{2,}', ' ', x).strip(' ,') or t

    labels = v['type_labels']
    ids = {t: 'n%03d' % i for i, t in enumerate(sorted(keep))}
    nodes = []
    for t in sorted(keep):
        n = keep[t]
        w = 0.3 + 0.7 * (deg[t] / mx) ** 0.75
        conns = [{'id': ids[b], 'proximity': p} for (a, b), p in edges.items() if a == t]
        conns += [{'id': ids[b], 'proximity': p} for (a, b), p in latent.items() if a == t]
        conns.sort(key=lambda c: c['id'])
        nodes.append({'id': ids[t], 'name': clean_title(t), 'category': category_of(n, v), 'weight': round(w, 2),
                      'meta': f"{labels.get(n['tipo'], n['tipo'] or 'nota')} · confiança {n['conf'] or 'n/d'}",
                      'connections': conns})

    # atividade semanal
    start_d = dt.date.fromisoformat(start or cfg['timeline']['start'])
    today = today or dt.date.today()
    alld = [dt.date.fromisoformat(x) for n in keep.values() for x in n['dates']]
    alld += [dt.date.fromisoformat(x) for x, _ in events]
    until_d = dt.date.fromisoformat(until) if until else max([x for x in alld if x <= today] or [today])
    nw = (until_d - start_d).days // 7 + 1
    weeks = [(start_d + dt.timedelta(days=7 * i)).isoformat() for i in range(nw)]

    def wk(ds):
        x = dt.date.fromisoformat(ds)
        if x > until_d:
            return None  # plano futuro não é atividade
        return max(0, (x - start_d).days // 7)

    act = {t: [0] * nw for t in keep}
    for t, n in keep.items():
        for ds in n['dates']:
            i = wk(ds)
            if i is not None:
                act[t][i] += 1
    for ds, links in events:
        i = wk(ds)
        if i is None:
            continue
        for link in set(links):
            if link in act:
                act[link][i] += 1
    by_id = {i: t for t, i in ids.items()}
    for nd in nodes:
        nd['act'] = act[by_id[nd['id']]]

    data = {'categories': cats, 'nodes': nodes, 'source': source, 'weeks': weeks, 'until': until_d.isoformat()}
    stats = dict(edges=len(edges), latent=len(latent), excluded=len(excluded), weeks=nw,
                 per_week=[sum(a[i] for a in act.values()) for i in range(nw)],
                 silent=sum(1 for a in act.values() if not sum(a)),
                 by_cat=collections.Counter(n['category'] for n in nodes),
                 top=[(clean_title(t), deg[t]) for t, _ in deg.most_common(12)],
                 isolated=[clean_title(t) for t in keep if deg[t] == 0 and not any(t in k for k in latent)])
    return data, stats, notes


def person_hits(data, notes, cfg, extra_names=()):
    """Tokens de nomes de pessoas (4+ letras) que aparecem no JSON. Lista vazia = ok."""
    gc, v = cfg['graph'], cfg['vault']
    ignore = {fold(x) for x in gc['person_scan_ignore']}
    toks = set()
    for p in (t for t, n in notes.items() if n['tipo'] == v['person_type']):
        for w in re.findall(r'[A-Za-zÀ-ÿ]{4,}', p):
            if fold(w) not in ignore:
                toks.add(fold(w))
    blob = fold(json.dumps(data, ensure_ascii=False))
    hits = sorted(w for w in toks if re.search(r'\b' + re.escape(w) + r'\b', blob))
    allow = {fold(x) for x in gc['person_scan_allow']}
    hits = [h for h in hits if h not in allow]
    for name in extra_names:
        f = fold(name.strip())
        if f and re.search(r'\b' + re.escape(f) + r'\b', blob):
            hits.append(f)
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--config', required=True)
    ap.add_argument('--vault', help='sobrepõe vault.path do config')
    ap.add_argument('--out', required=True)
    ap.add_argument('--source', required=True, help='rótulo exibido no topo da página')
    ap.add_argument('--until', default=None, help='AAAA-MM-DD, fim da última semana (padrão: data mais recente até hoje)')
    ap.add_argument('--start', default=None, help='segunda-feira da primeira semana (padrão: timeline.start do config)')
    args = ap.parse_args(argv)
    over = {'vault': {'path': os.path.abspath(args.vault)}} if args.vault else None
    cfg = cfgmod.load(args.config, over)
    if not cfg['vault']['path']:
        ap.error('informe --vault ou vault.path no config')
    if not (args.start or cfg['timeline']['start']):
        ap.error('informe --start ou timeline.start no config')
    data, st, notes = build(cfg, args.source, args.until, args.start)
    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    print('nós', len(data['nodes']), '| diretas', st['edges'], '| latentes', st['latent'], '| excluídas', st['excluded'])
    print('semanas', st['weeks'], '| registros por semana', st['per_week'], '| temas sem registro', st['silent'])
    print(st['by_cat'])
    print('top peso:', st['top'])
    print('isolados:', st['isolated'])
    extra = []
    sn = cfg['private']['sensitive_names']
    if sn and os.path.exists(sn):
        with open(sn, encoding='utf-8') as fh:
            extra = [x for x in fh.read().split('\n') if x.strip() and not x.startswith('#')]
    hits = person_hits(data, notes, cfg, extra)
    print('nomes de pessoa encontrados no JSON:', hits)
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
