"""Gera extratos redigidos de mensagens novas, um arquivo por segmento do cérebro.

Uso:
  python3 pipeline/prep_messages.py --config config/config.json --new novas.ndjson --out extratos/

Entrada: NDJSON, uma mensagem por linha, com os campos
  chat_jid, chat_name, from_me (bool), sender_name, sender_jid, text, transcript (opcional),
  timestamp (ISO 8601 em UTC, "AAAA-MM-DDTHH:MM:SS...").
Arquivos privados (fora do git, ver docs/PRIVACIDADE.md):
  private.chat_map  {"by_jid": {jid: {"dom", "sub"}}, "by_name": {nome: {"dom", "sub"}}}
  private.aliases   {jid: {"alias", "name"}}  conversas sigilosas trocadas por alias estável
Efeitos:
  - Conversa de subcategoria sigilosa, ou conversa 1:1 desconhecida cujo nome casa com
    messages.sensitive_name_regex, ganha alias novo (prefixo messages.new_alias_prefix) gravado em aliases.
  - O texto passa por redact() e é cortado em messages.max_chars.
  - JID nunca sai no extrato: remetente sem nome vira '?' e conversa sem nome vira '[sem nome]'.
    Nome igual a um JID conta como sem nome. Nomes de remetente e de conversa também passam por
    redact() (contato salvo como número); conversas cujo nome a redação alterou seguem separadas.
  - Grupos com mais de group_sample.threshold mensagens viram amostra: todas as do dono mais
    keep_others das demais com min_len caracteres ou mais (semente fixa, resultado reprodutível).
"""
import argparse
import collections
import datetime as dt
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as cfgmod  # noqa: E402
from redact import redact  # noqa: E402

PLACEHOLDER = re.compile(r'(?i)sent (image|sticker|document|video|audio|gif|location)')
NO_SENDER, NO_CHAT = '?', '[sem nome]'
JID_LIKE = re.compile(r'\S+@\S+')


def shown_name(name, empty):
    """Nome que pode ir ao extrato: redigido, ou o marcador `empty` se faltar ou for um JID."""
    return empty if not name or JID_LIKE.fullmatch(name) else redact(name)


def segment_of(dom, sub, disp, mc, sens):
    if sens.match(disp) or str(sub).startswith(tuple(mc['sensitive_sub_prefixes']) or ('\0',)):
        return mc['sensitive_segment']
    for rule in mc['segments']:
        if 'sub' in rule and sub not in rule['sub']:
            continue
        if 'dom' in rule and dom not in rule['dom']:
            continue
        if 'display' in rule and disp not in rule['display']:
            continue
        return rule['out']
    return mc['default_segment']


class Prep:
    def __init__(self, cfg):
        self.mc = cfg['messages']
        p = cfg['private']
        with open(p['chat_map'], encoding='utf-8') as fh:
            self.cm = json.load(fh)
        self.alias_path = p['aliases']
        if os.path.exists(self.alias_path):
            with open(self.alias_path, encoding='utf-8') as fh:
                self.keys = json.load(fh)
        else:
            self.keys = {}
        self.sens = re.compile(self.mc['sensitive_alias_regex'])
        nr = self.mc['sensitive_name_regex']
        self.lawyer = re.compile(nr) if nr else None
        pre = self.mc['new_alias_prefix'] + '-'
        self.nxt = 1 + max([int(v['alias'].split('-')[1]) for v in self.keys.values() if v['alias'].startswith(pre)] + [0])
        self.tz = dt.timedelta(hours=self.mc['timezone_offset_hours'])

    def info(self, r):
        j = r['chat_jid']
        nm = r.get('chat_name') or j
        c = self.cm['by_jid'].get(j) or self.cm['by_name'].get(nm)
        un, fb = self.mc['unclassified'], self.mc['aliased_fallback']
        d, s = (c['dom'], c['sub']) if c else (un['dom'], un['sub'])
        if j in self.keys:
            return self.keys[j]['alias'], (d if c else fb['dom']), (s if c else fb['sub'])
        return nm, d, s

    def ensure_alias(self, r, sub):
        j = r['chat_jid']
        nm = r.get('chat_name') or j
        if j in self.keys:
            return self.keys[j]['alias']
        known = j in self.cm['by_jid'] or nm in self.cm['by_name']
        pref = tuple(self.mc['sensitive_sub_prefixes'])
        by_sub = bool(pref) and str(sub).startswith(pref)
        by_name = (not known and not j.endswith('@g.us') and self.lawyer is not None and self.lawyer.search(nm))
        if by_sub or by_name:
            al = f"{self.mc['new_alias_prefix']}-{self.nxt:02d}"
            self.nxt += 1
            self.keys[j] = {'alias': al, 'name': nm}
            return al
        return None

    def run(self, lines):
        mc = self.mc
        out = collections.defaultdict(lambda: collections.defaultdict(list))
        n_in = 0
        for line in lines:
            r = json.loads(line)
            n_in += 1
            disp, d, s = self.info(r)
            al = self.ensure_alias(r, s)
            if al:
                disp = al
            t = r.get('text') or ''
            if PLACEHOLDER.fullmatch(t.strip()) or t == '(message)' or not t.strip():
                if r.get('transcript'):
                    t = '[áudio] ' + r['transcript']
                else:
                    continue
            t = redact(t)[:mc['max_chars']]
            if r['from_me']:
                who = mc['me_label']
            elif self.sens.match(disp):
                who = mc['sensitive_label']
            else:
                who = shown_name(r.get('sender_name'), NO_SENDER)[:18]
            ts = (dt.datetime.strptime(r['timestamp'][:19], '%Y-%m-%dT%H:%M:%S') + self.tz).strftime('%m-%d %H:%M')
            raw = r.get('chat_name')
            shown = disp if al or r['chat_jid'] in self.keys else shown_name(raw, NO_CHAT)
            # nome ausente ou alterado pela redação: o JID separa as conversas na chave e nunca é escrito
            key = (shown, d, s, r['chat_jid'].endswith('@g.us'), r['chat_jid'] if shown not in (raw, disp) else None)
            out[segment_of(d, s, disp, mc, self.sens)][key].append(f'{ts} {who}: {t}')
        return out, n_in

    def write(self, out, folder):
        mc, gs = self.mc, self.mc['group_sample']
        os.makedirs(folder, exist_ok=True)
        names = {mc['sensitive_segment'], mc['default_segment']} | {r['out'] for r in mc['segments']}
        for f in os.listdir(folder):
            if f.endswith('.txt') and f[:-4] in names:
                os.remove(os.path.join(folder, f))
        me = f" {mc['me_label']}: "
        report = []
        for sg, chats in out.items():
            lines = []
            for (disp, d, s, g, _jid), ls in sorted(chats.items(), key=lambda kv: kv[1][0]):
                if g and len(ls) > gs['threshold']:
                    random.seed(gs['seed'])
                    mine = [x for x in ls if me in x]
                    oth = [x for x in ls if me not in x and len(x) > gs['min_len']]
                    ls = sorted(mine + random.sample(oth, min(gs['keep_others'], len(oth))))
                lines.append(f"\n===== CONVERSA: {disp} | {d} / {s} | {'grupo' if g else '1:1'} | linhas: {len(ls)} =====")
                lines += ls
            with open(os.path.join(folder, sg + '.txt'), 'w', encoding='utf-8') as fh:
                fh.write('\n'.join(lines))
            report.append(f'{sg}: {sum(len(v) for v in chats.values())} msgs, {len(chats)} conversas')
        with open(self.alias_path, 'w', encoding='utf-8') as fh:
            json.dump(self.keys, fh, ensure_ascii=False)
        return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--config', required=True)
    ap.add_argument('--new', required=True, help='NDJSON com as mensagens novas')
    ap.add_argument('--out', required=True, help='pasta dos extratos')
    a = ap.parse_args(argv)
    cfg = cfgmod.load(a.config)
    prep = Prep(cfg)
    with open(a.new, encoding='utf-8') as fh:
        out, n_in = prep.run(fh)
    for line in prep.write(out, a.out):
        print(line)
    print('mensagens lidas:', n_in, '| aliases sigilosos:', len(prep.keys))
    return 0


if __name__ == '__main__':
    sys.exit(main())
