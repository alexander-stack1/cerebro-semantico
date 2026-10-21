"""Reconstrói a linha do tempo a partir das notas "Eventos ...".

Uso:
  python3 pipeline/timeline.py --config config/config.json --csv eventos.csv --until AAAA-MM-DD [--vault DIR]

Grava:
  - CSV com data, domínio, evento, nota e área;
  - na pasta timeline.folder do vault: uma nota por mês, "Linha do tempo Próximos" (datas
    depois de --until) e o índice "Linha do tempo" com a contagem por mês e domínio.
"""
import argparse
import collections
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from vault import read_event_rows  # noqa: E402

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
         'Novembro', 'Dezembro']


def month_name(ym):
    return f'{MESES[int(ym[5:]) - 1]} {ym[:4]}'


def _rel(links):
    return '[' + ', '.join(f'"{x}"' for x in links) + ']'


def _lig(lines):
    return '\n## Ligações\n' + '\n'.join(lines)


def build(vault, cfg, csv_path, until):
    tc, v = cfg['timeline'], cfg['vault']
    ev = sorted(read_event_rows(vault, v['ignore_files'], v['events_prefix']))
    labels = tc['area_labels']
    with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['data', 'dominio', 'evento', 'nota', 'area'])
        for a, b, c, dd, e in ev:
            w.writerow([a, b, c, re.sub(r'[\[\]]', '', dd), labels.get(e, e)])
    out_dir = os.path.join(vault, tc['folder'])
    os.makedirs(out_dir, exist_ok=True)
    first = tc['months_from'] or (ev[0][0][:7] if ev else until[:7])
    months = sorted({e[0][:7] for e in ev if e[0][:7] >= first and e[0] <= until[:7] + '-31'})
    lk = tc['links']
    rel = tc['related']
    for ym in months:
        rows = [e for e in ev if e[0].startswith(ym)]
        out = [f'---\ntipo: periodo\ndominio: Profissional\ntags: [linha-do-tempo, {ym}]\nrelacionados: {_rel(rel["month"])}\n'
               f'periodo: {ym}\nconfianca: media\nfonte: "{tc["fonte"]}"\n---\n# Linha do tempo {month_name(ym)}\n\n'
               f'{len(rows)} eventos datados, ordenados por dia. Cada linha liga à nota que a sustenta.\n']
        day = None
        for a, b, c, dd, _e in rows:
            if a != day:
                out.append(f'\n## {a}')
                day = a
            out.append(f'- {b}: {c} {dd}')
        out.append(_lig(lk['month']))
        with open(os.path.join(out_dir, f'Linha do tempo {month_name(ym)}.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(out) + '\n')
    fut = [e for e in ev if e[0] > until]
    out = ['---\ntipo: periodo\ndominio: Profissional\ntags: [linha-do-tempo, futuro]\nrelacionados: ' + _rel(rel['future']) +
           '\nperiodo: depois de ' + until + '\nconfianca: media\nfonte: "' + tc['fonte'] + '"\n---\n'
           '# Linha do tempo Próximos\n\nCompromissos e prazos futuros citados nas conversas. '
           'São planos ditos no chat, não fatos consumados.\n']
    day = None
    for a, b, c, dd, _e in fut:
        if a != day:
            out.append(f'\n## {a}')
            day = a
        out.append(f'- {b}: {c} {dd}')
    out.append(_lig(lk['future']))
    with open(os.path.join(out_dir, 'Linha do tempo Próximos.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out) + '\n')
    cnt = collections.Counter((e[0][:7], e[1]) for e in ev)
    doms = tc['domains']
    tab = ['| Mês | ' + ' | '.join(doms) + ' | Total |', '|' + '---|' * (len(doms) + 2)]
    for ym in months:
        tab.append(f'| [[Linha do tempo {month_name(ym)}]] | ' + ' | '.join(str(cnt[(ym, d)]) for d in doms) +
                   f' | {sum(1 for e in ev if e[0].startswith(ym))} |')
    past = [e for e in ev if e[0] <= until]
    span = f'de {past[0][0]} a {past[-1][0]}' if past else 'sem datas'
    start = tc['period_start'] or (past[0][0] if past else until)
    nl = chr(10)
    index = (f'---\ntipo: periodo\ndominio: Profissional\ntags: [linha-do-tempo]\nrelacionados: {_rel(rel["index"])}\n'
             f'periodo: {start} a {until}\nconfianca: media\nfonte: "{tc["fonte"]}"\n---\n# Linha do tempo\n\n'
             f'{len(past)} eventos datados que {tc["source_label"]} comprova, {span}. '
             f'Mais {len(fut)} compromissos futuros em [[Linha do tempo Próximos]]. Última atualização: {until}.\n\n'
             f'{nl.join(tab)}\n\n'
             f'A tabela por mês inclui os eventos futuros do mês corrente. Linhas com domínio próprio da área '
             f'(ex.: Mentoria) ficam fora das {len(doms)} colunas, mas entram no total.\n\n'
             f'Arquivo de dados: {os.path.basename(csv_path)}.\n{_lig(lk["index"])}\n')
    with open(os.path.join(out_dir, 'Linha do tempo.md'), 'w', encoding='utf-8') as fh:
        fh.write(index)
    return dict(events=len(ev), past=len(past), future=len(fut), months=months)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--config', required=True)
    ap.add_argument('--vault', help='sobrepõe vault.path do config')
    ap.add_argument('--csv', required=True)
    ap.add_argument('--until', required=True, help='AAAA-MM-DD; datas posteriores vão para "Próximos"')
    a = ap.parse_args(argv)
    cfg = cfgmod.load(a.config)
    vault = os.path.abspath(a.vault) if a.vault else cfg['vault']['path']
    if not vault:
        ap.error('informe --vault ou vault.path no config')
    st = build(vault, cfg, a.csv, a.until)
    print('eventos', st['events'], '| passados', st['past'], '| futuros', st['future'], '| meses', st['months'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
