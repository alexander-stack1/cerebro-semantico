"""Gera o vault fictício de exemplo em examples/vault (determinístico, semente fixa).

Uso: python3 examples/gerar_vault_exemplo.py [--out examples/vault]

Tudo aqui é inventado: a dona do vault (Bia), as pessoas (Marta, Rui, Dona Lia) e os temas.
O vault cobre 14 semanas, de 2026-07-13 a 2026-10-18, e tem eventos futuros para a
linha do tempo testar a nota "Próximos".
"""
import argparse
import datetime as dt
import os
import random
import shutil

START = dt.date(2026, 7, 13)
WEEKS = 14

# pasta: (domínio padrão do frontmatter, nome da nota de eventos)
FOLDERS = {
    '10_Trabalho': ('Profissional', 'Eventos Trabalho'),
    '20_Projetos': ('Profissional', 'Eventos Projetos'),
    '30_Estudos': ('Profissional', 'Eventos Estudos'),
    '40_Comunicacao': ('Profissional', 'Eventos Comunicação'),
    '50_Casa_Familia': ('Pessoal', 'Eventos Casa'),
    '60_Financas_Lazer': ('Financeiro', 'Eventos Finanças e Lazer'),
    '70_Saude_Rotina': ('Pessoal', 'Eventos Saúde'),
}

# título, pasta, tipo, domínio (None = padrão da pasta), tags, perfil de atividade
TOPICS = [
    ('Relatório mensal da equipe', '10_Trabalho', 'projeto', None, ['relatorio', 'prazos', 'equipe'], ('mensal',)),
    ('Reunião semanal de planejamento', '10_Trabalho', 'rotina', None, ['reuniao', 'prazos'], ('constante', 1.2)),
    ('Migração do sistema de chamados', '10_Trabalho', 'projeto', None, ['sistema', 'prazos', 'equipe'], ('pico', 8, 3)),
    ('Atendimento a fornecedores', '10_Trabalho', 'fluxo', None, ['fornecedores', 'contratos'], ('constante', 0.6)),
    ('Avaliação de desempenho com a Marta', '10_Trabalho', 'decisao', None, ['equipe', 'carreira'], ('pico', 11, 1)),
    ('Plano de carreira', '10_Trabalho', 'tema', None, ['carreira', 'estudos'], ('subindo',)),
    ('Horta no quintal', '20_Projetos', 'projeto', None, ['horta', 'casa'], ('caindo',)),
    ('Blog de receitas', '20_Projetos', 'projeto', None, ['escrita', 'receitas'], ('constante', 0.5)),
    ('Restauração da bicicleta antiga', '20_Projetos', 'projeto', None, ['bicicleta', 'oficina'], ('pico', 5, 2)),
    ('Aplicativo de lista de compras', '20_Projetos', 'projeto', None, ['sistema', 'compras'], ('subindo',)),
    ('Painel de metas', '00_Mapa', 'tema', 'Pessoal', ['metas', 'carreira'], ('mensal',)),
    ('Curso de fotografia', '30_Estudos', 'projeto', None, ['fotografia', 'curso'], ('pico', 6, 4)),
    ('Inglês para reuniões', '30_Estudos', 'rotina', None, ['idiomas', 'reuniao'], ('constante', 0.8)),
    ('Leitura do mês', '30_Estudos', 'rotina', None, ['leitura', 'livros'], ('constante', 0.4)),
    ('Certificação em gestão de projetos', '30_Estudos', 'projeto', None, ['carreira', 'curso', 'prazos'], ('subindo',)),
    ('Oficina de escrita', '30_Estudos', 'tema', None, ['escrita', 'curso'], ('pico', 2, 2)),
    ('Respostas rápidas para clientes', '40_Comunicacao', 'resposta', None, ['clientes', 'escrita'], ('constante', 0.7)),
    ('Tom de voz nos e-mails', '40_Comunicacao', 'voz', None, ['escrita', 'clientes'], ('constante', 0.3)),
    ('Apresentação trimestral', '40_Comunicacao', 'projeto', None, ['apresentacao', 'relatorio'], ('pico', 12, 2)),
    ('Grupo do condomínio', '40_Comunicacao', 'tema', 'Pessoal', ['condominio', 'vizinhos'], ('constante', 0.5)),
    ('Mudança de quarto do Rui', '50_Casa_Familia', 'projeto', None, ['casa', 'familia', 'obra'], ('pico', 3, 2)),
    ('Almoço de domingo em família', '50_Casa_Familia', 'rotina', None, ['familia', 'receitas'], ('constante', 0.9)),
    ('Reforma do banheiro', '50_Casa_Familia', 'projeto', None, ['casa', 'obra', 'contratos'], ('pico', 9, 3)),
    ('Cuidados com o cachorro', '50_Casa_Familia', 'rotina', None, ['pet', 'casa'], ('constante', 0.6)),
    ('Aniversário da mãe', '50_Casa_Familia', 'evento', None, ['familia', 'festa'], ('pico', 10, 1)),
    ('Divisão das tarefas de casa', '50_Casa_Familia', 'decisao', None, ['casa', 'familia'], ('caindo',)),
    ('Orçamento doméstico', '60_Financas_Lazer', 'financeiro', 'Financeiro', ['orcamento', 'compras'], ('mensal',)),
    ('Reserva de emergência', '60_Financas_Lazer', 'financeiro', 'Financeiro', ['investimentos', 'orcamento'], ('constante', 0.3)),
    ('Imposto de renda', '60_Financas_Lazer', 'financeiro', 'Financeiro', ['impostos', 'prazos'], ('caindo',)),
    ('Troca do carro', '60_Financas_Lazer', 'decisao', 'Financeiro', ['carro', 'orcamento'], ('pico', 7, 2)),
    ('Viagem de férias para a serra', '60_Financas_Lazer', 'viagem', 'Viagens', ['viagem', 'ferias'], ('pico', 4, 2)),
    ('Clube do livro', '60_Financas_Lazer', 'lazer', 'Lazer', ['livros', 'amigos'], ('constante', 0.5)),
    ('Futebol de quinta', '60_Financas_Lazer', 'lazer', 'Lazer', ['esporte', 'amigos'], ('constante', 0.9)),
    ('Trilhas no fim de semana', '60_Financas_Lazer', 'lazer', 'Lazer', ['trilha', 'esporte'], ('subindo',)),
    ('Festival de cinema', '60_Financas_Lazer', 'lazer', 'Lazer', ['cinema', 'amigos'], ('pico', 13, 1)),
    ('Corrida pela manhã', '70_Saude_Rotina', 'rotina', None, ['esporte', 'corrida'], ('subindo',)),
    ('Rotina de sono', '70_Saude_Rotina', 'rotina', None, ['sono', 'rotina'], ('constante', 0.4)),
    ('Consultas de rotina', '70_Saude_Rotina', 'agenda', None, ['saude', 'agenda'], ('mensal',)),
    ('Alimentação da semana', '70_Saude_Rotina', 'rotina', None, ['receitas', 'compras'], ('constante', 0.7)),
    ('Pausas no trabalho', '70_Saude_Rotina', 'rotina', None, ['rotina', 'equipe'], ('constante', 0.5)),
]

# ligações entre temas: (origem, destino, recíproca?)
LINKS = [
    (0, 1, True), (0, 2, False), (1, 2, True), (2, 3, False), (0, 4, True), (4, 5, True), (5, 14, True), (5, 12, False),
    (3, 16, False), (1, 39, True), (2, 9, False),
    (6, 7, False), (7, 21, True), (8, 33, False), (9, 26, True), (10, 5, True), (10, 6, False), (10, 27, False),
    (11, 15, True), (12, 13, False), (13, 31, True), (14, 2, False), (15, 7, True), (12, 1, False),
    (16, 17, True), (18, 0, True), (18, 16, False), (19, 23, False), (19, 22, True),
    (20, 25, True), (21, 24, True), (22, 27, False), (23, 20, False), (24, 21, False), (25, 26, False),
    (26, 27, True), (27, 29, False), (28, 30, True), (29, 26, False),
    (30, 33, True), (31, 13, False), (32, 34, True), (33, 35, True), (34, 30, False),
    (35, 36, True), (36, 38, True), (37, 39, False), (38, 21, False), (39, 1, False), (39, 36, False),
    (1, 12, True), (4, 39, False), (6, 38, True), (6, 23, False), (7, 38, True), (8, 29, False), (9, 38, False),
    (10, 14, True), (10, 35, False), (11, 30, True), (11, 34, False), (12, 14, False), (13, 15, False),
    (14, 18, False), (17, 18, True), (19, 20, False), (20, 22, True), (21, 32, False), (23, 35, True),
    (24, 26, False), (25, 23, False), (26, 29, True), (27, 30, False), (28, 26, True), (31, 34, True),
    (32, 35, True), (33, 35, False), (36, 39, True), (37, 36, False), (37, 38, True), (2, 18, False),
]

PEOPLE = {
    'Marta': ('colega de trabalho', [0, 2, 4, 18]),
    'Rui': ('irmão', [20, 21, 32]),
    'Dona Lia': ('vizinha', [19, 23, 6]),
}

FACTS = ['Atualizou o plano.', 'Combinou o próximo passo.', 'Fechou uma pendência.', 'Anotou uma ideia nova.',
         'Revisou o que estava parado.', 'Marcou uma data.', 'Pediu ajuda e recebeu resposta.', 'Mudou de prioridade.']
EVENTS = ['Concluiu uma etapa', 'Começou uma frente nova', 'Teve uma conversa decisiva', 'Ajustou o prazo',
          'Registrou um resultado']
LABEL_DOM = {'Profissional': 'Profissional', 'Pessoal': 'Pessoal', 'Financeiro': 'Financeiro', 'Viagens': 'Viagens',
             'Lazer': 'Lazer'}


def rate(profile, w):
    kind = profile[0]
    if kind == 'constante':
        return profile[1]
    if kind == 'subindo':
        return 0.1 + 1.4 * w / (WEEKS - 1)
    if kind == 'caindo':
        return 1.5 - 1.4 * w / (WEEKS - 1)
    if kind == 'mensal':
        return 1.6 if w % 4 == 0 else 0.15
    if kind == 'pico':
        center, width = profile[1], profile[2]
        return 2.4 if abs(w - center) < width else 0.1
    raise ValueError(kind)


def draws(rng, lam):
    """Número de registros na semana: Poisson simples com teto 4."""
    n, p, limit = 0, 1.0, pow(2.718281828, -lam)
    while True:
        p *= rng.random()
        if p <= limit or n >= 4:
            return n
        n += 1


def front(tipo, dom, tags, rel, conf='media'):
    rel_s = ', '.join(f'"[[{x}]]"' for x in rel)
    return (f'---\ntipo: {tipo}\ndominio: {dom}\ntags: [{", ".join(tags)}]\nrelacionados: [{rel_s}]\n'
            f'periodo: 2026-07-13 a 2026-10-18\nconfianca: {conf}\nfonte: "Notas de exemplo"\n---\n')


def generate(out):
    rng = random.Random(42)
    if os.path.isdir(out):
        shutil.rmtree(out)
    for f in list(FOLDERS) + ['00_Mapa', '05_Pessoas']:
        os.makedirs(os.path.join(out, f), exist_ok=True)
    links = {i: [] for i in range(len(TOPICS))}
    for a, b, both in LINKS:
        links[a].append(b)
        if both:
            links[b].append(a)
    people_of = {i: [p for p, (_, ts) in PEOPLE.items() if i in ts] for i in range(len(TOPICS))}
    events = {f: [] for f in FOLDERS}
    for i, (title, folder, tipo, dom, tags, prof) in enumerate(TOPICS):
        dom = dom or FOLDERS.get(folder, ('Pessoal',))[0]
        facts = []
        for w in range(WEEKS):
            for _ in range(draws(rng, rate(prof, w))):
                day = START + dt.timedelta(days=7 * w + rng.randrange(7))
                facts.append((day.isoformat(), rng.choice(FACTS)))
        facts.sort()
        targets = [TOPICS[j][0] for j in links[i]] + people_of[i]
        conf = 'alta' if len(facts) > 12 else 'media'
        body = [front(tipo, dom, tags, targets[:4], conf), f'# {title}\n',
                f'Nota de exemplo sobre {title.lower()}. Tudo aqui é fictício.\n', '## Fatos']
        body += [f'- {d}: {t}' for d, t in facts] or ['- sem registro datado no período']
        body += ['', '## Ligações'] + [f'[[{x}]] porque os dois assuntos andam juntos.' for x in targets]
        with open(os.path.join(out, folder, title + '.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(body) + '\n')
        ev_folder = folder if folder in FOLDERS else '20_Projetos'
        for d, _ in facts[::3]:
            events[ev_folder].append((d, LABEL_DOM[dom], rng.choice(EVENTS), title))
    # eventos futuros (depois de 2026-10-18) para a nota "Próximos" da linha do tempo
    events['10_Trabalho'].append(('2026-10-27', 'Profissional', 'Entrega da apresentação', 'Apresentação trimestral'))
    events['50_Casa_Familia'].append(('2026-11-08', 'Pessoal', 'Fim da reforma previsto', 'Reforma do banheiro'))
    for folder, (dom, name) in FOLDERS.items():
        rows = sorted(events[folder])
        body = [front('eventos', dom, ['eventos'], [r[3] for r in rows[:3]]), f'# {name}\n', 'Eventos datados da área.\n']
        body += [f'- {d} | {dm} | {e} | [[{t}]]' for d, dm, e, t in rows]
        with open(os.path.join(out, folder, name + '.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(body) + '\n')
    for person, (role, ts) in PEOPLE.items():
        tl = [TOPICS[i][0] for i in ts]
        body = [front('pessoa', 'Pessoal', ['pessoa'], tl[:3]), f'# {person}\n', f'Pessoa fictícia: {role}.\n',
                '## Ligações'] + [f'[[{x}]] porque aparece nesse assunto.' for x in tl]
        with open(os.path.join(out, '05_Pessoas', person + '.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(body) + '\n')
    hubs = []
    for folder in FOLDERS:
        name = 'Hub ' + folder.split('_', 1)[1].replace('_', ' ')
        hubs.append(name)
        tl = [t[0] for t in TOPICS if t[1] == folder]
        body = [front('hub', FOLDERS[folder][0], ['hub'], tl[:3]), f'# {name}\n', 'Índice da área.\n', '## Ligações']
        body += [f'[[{x}]] porque pertence à área.' for x in tl]
        with open(os.path.join(out, folder, name + '.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(body) + '\n')
    body = [front('hub', 'Pessoal', ['mapa'], hubs[:3]), '# Mapa do cérebro\n', 'Índice geral do vault de exemplo.\n',
            '## Ligações'] + [f'[[{x}]] porque é uma área.' for x in hubs] + ['[[Painel de metas]] porque resume as metas.']
    with open(os.path.join(out, '00_Mapa', 'Mapa do cérebro.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(body) + '\n')
    with open(os.path.join(out, 'LEIA-ME.md'), 'w', encoding='utf-8') as fh:
        fh.write('# Vault de exemplo\n\nGerado por examples/gerar_vault_exemplo.py. Conteúdo fictício.\n')
    return sum(len(fs) for _, _, fs in os.walk(out))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--out', default=os.path.join(here, 'vault'))
    a = ap.parse_args()
    print('arquivos gerados:', generate(a.out))
