"""Carrega e valida a configuração do pipeline.

A configuração é um JSON. O exemplo comentado fica em config/config.example.json.
Toda chave ausente recebe o valor padrão de DEFAULTS. A validação falha cedo,
com mensagem clara, em vez de gerar um grafo errado em silêncio.
"""
import copy
import json
import os
import re

LOBES = ('frontalE', 'frontalD', 'parietalE', 'parietalD', 'temporalE', 'temporalD', 'limbico', 'posterior')

DEFAULTS = {
    'categories': {},
    'vault': {
        'path': None,
        'ignore_files': ['LEIA-ME.md', 'README.md'],
        'events_prefix': 'Eventos',
        'folders': {},
        'folder_by_field': {},
        'title_category': {},
        'person_type': 'pessoa',
        'exclude_types': ['pessoa', 'hub', 'periodo', 'eventos', 'linha-do-tempo', 'pendencias'],
        'exclude_titles': [],
        'exclude_title_prefixes': ['Eventos', 'Linha do tempo', 'Pendências', 'Hub '],
        'latent_skip_types': ['hub', 'periodo', 'eventos', 'linha-do-tempo'],
        'latent_skip_prefixes': ['Eventos', 'Linha do tempo', 'Hub ', 'Mapa'],
        'stop_tags': [],
        'type_labels': {},
    },
    'graph': {
        'rename': {},
        'owner_names': [],
        'person_scan_ignore': [],
        'person_scan_allow': [],
        'max_latent_per_node': 2,
        'latent_max_shared': 14,
    },
    'timeline': {
        'start': None,
        'area_labels': {},
        'folder': '90_Linha_do_tempo',
        'months_from': None,
        'period_start': None,
        'domains': ['Profissional', 'Pessoal', 'Lazer', 'Viagens', 'Financeiro'],
        'source_label': 'as conversas',
        'fonte': 'Eventos das áreas do cérebro',
        'related': {'month': ['[[Linha do tempo]]'], 'future': ['[[Linha do tempo]]'], 'index': []},
        'links': {'month': ['[[Linha do tempo]] porque reúne os meses.'],
                  'future': ['[[Linha do tempo]] porque reúne os meses.'],
                  'index': ['[[Linha do tempo Próximos]] porque guarda o que ainda vai acontecer.']},
    },
    'messages': {
        'timezone_offset_hours': 0,
        'max_chars': 500,
        'me_label': 'EU',
        'sensitive_label': 'ELE',
        'sensitive_alias_regex': r'^(Cliente|Contraparte|Colega|Novo)-\d+$',
        'new_alias_prefix': 'Novo',
        'sensitive_sub_prefixes': [],
        'sensitive_name_regex': None,
        'unclassified': {'dom': 'Não classificado', 'sub': 'Revisar'},
        'aliased_fallback': {'dom': 'Profissional', 'sub': 'Sigiloso (regra)'},
        'sensitive_segment': 'N0_sigiloso',
        'segments': [],
        'default_segment': 'N9_outros',
        'group_sample': {'threshold': 400, 'keep_others': 150, 'min_len': 70, 'seed': 3},
    },
    'lint': {
        'forbidden_phrases': [],
        'phrase_exempt_files_regex': None,
        'flag_dashes': True,
        'sensitive_name_min_len': 8,
    },
    'private': {
        'chat_map': '../private/chat_map.json',
        'aliases': '../private/aliases.json',
        'sensitive_names': None,
    },
}


class ConfigError(ValueError):
    pass


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and k not in ('categories', 'folders', 'rename',
                                                                          'title_category', 'folder_by_field',
                                                                          'type_labels', 'area_labels'):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def validate(cfg):
    cats = cfg['categories']
    if not cats:
        raise ConfigError('config.categories está vazio: defina ao menos uma categoria')
    for key, c in cats.items():
        for f in ('label', 'color', 'lobe'):
            if f not in c:
                raise ConfigError(f'categoria "{key}" sem o campo "{f}"')
        if c['lobe'] not in LOBES:
            raise ConfigError(f'categoria "{key}": lobo "{c["lobe"]}" inválido. Use um de {", ".join(LOBES)}')
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', c['color']):
            raise ConfigError(f'categoria "{key}": cor "{c["color"]}" fora do formato #RRGGBB')
    v = cfg['vault']
    allowed = set(cats) | {None}
    for folder, cat in v['folders'].items():
        if cat not in allowed:
            raise ConfigError(f'vault.folders["{folder}"] aponta para categoria inexistente: {cat}')
    for folder, rule in v['folder_by_field'].items():
        if 'field' not in rule or 'map' not in rule:
            raise ConfigError(f'vault.folder_by_field["{folder}"] precisa de "field" e "map"')
        for cat in list(rule['map'].values()) + [rule.get('default')]:
            if cat not in allowed:
                raise ConfigError(f'vault.folder_by_field["{folder}"] aponta para categoria inexistente: {cat}')
    for title, cat in v['title_category'].items():
        if cat not in allowed:
            raise ConfigError(f'vault.title_category["{title}"] aponta para categoria inexistente: {cat}')
    for seg in cfg['messages']['segments']:
        if 'out' not in seg:
            raise ConfigError('messages.segments: cada regra precisa de "out"')
    return cfg


def load(path, overrides=None):
    """Lê o JSON, aplica os padrões e valida.

    Caminhos relativos (vault.path e a seção private) partem da pasta do arquivo de config.
    """
    with open(path, encoding='utf-8') as fh:
        raw = json.load(fh)
    raw = _strip_notes(raw)
    cfg = _merge(DEFAULTS, raw)
    cfg = _merge(cfg, overrides or {})
    base = os.path.dirname(os.path.abspath(path))
    for k, p in cfg['private'].items():
        if p and not os.path.isabs(p):
            cfg['private'][k] = os.path.normpath(os.path.join(base, p))
    if cfg['vault']['path'] and not os.path.isabs(cfg['vault']['path']):
        cfg['vault']['path'] = os.path.normpath(os.path.join(base, cfg['vault']['path']))
    return validate(cfg)


def _strip_notes(raw):
    """Remove chaves de comentário ("_..."), no topo e dentro de cada seção."""
    out = {}
    for k, v in raw.items():
        if k.startswith('_'):
            continue
        out[k] = {kk: vv for kk, vv in v.items() if not kk.startswith('_')} if isinstance(v, dict) else v
    return out
