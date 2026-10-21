import datetime as dt
import filecmp
import json
import os
import subprocess
import sys
import unittest

import _util
import build_graph
from config import ConfigError

SOURCE = 'Vault de exemplo · 13/07 a 18/10/2026'


class GoldenTest(unittest.TestCase):
    """O grafo de exemplo versionado precisa sair igual do vault de exemplo versionado."""

    def test_sample_graph_reproduz(self):
        with _util.TempDir() as tmp:
            out = os.path.join(tmp, 'g.json')
            r = subprocess.run([sys.executable, os.path.join(_util.PIPE, 'build_graph.py'), '--config', _util.CONFIG,
                                '--out', out, '--source', SOURCE, '--until', '2026-10-18'],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(filecmp.cmp(out, os.path.join(_util.EXAMPLES, 'sample_graph.json'), shallow=False),
                            'examples/sample_graph.json desatualizado: rode o comando do README')

    def test_vault_de_exemplo_reproduz(self):
        sys.path.insert(0, _util.EXAMPLES)
        import gerar_vault_exemplo as gen
        with _util.TempDir() as tmp:
            gen.generate(os.path.join(tmp, 'v'))
            cmp = filecmp.dircmp(os.path.join(tmp, 'v'), os.path.join(_util.EXAMPLES, 'vault'))
            diffs = []

            def walk(c, base=''):
                diffs.extend(os.path.join(base, x) for x in c.diff_files + c.left_only + c.right_only)
                for name, sub in c.subdirs.items():
                    walk(sub, os.path.join(base, name))
            walk(cmp)
            self.assertEqual(diffs, [], 'examples/vault desatualizado: rode examples/gerar_vault_exemplo.py')


class RegrasTest(unittest.TestCase):
    def setUp(self):
        self.cfg = _util.load_example()
        self.data, self.st, self.notes = build_graph.build(self.cfg, SOURCE, until='2026-10-18')
        self.by_name = {n['name']: n for n in self.data['nodes']}

    def test_pessoas_e_indices_ficam_fora(self):
        names = set(self.by_name)
        for t in ('Marta', 'Rui', 'Dona Lia', 'Mapa do cérebro', 'Hub Trabalho', 'Eventos Trabalho'):
            self.assertNotIn(t, names)

    def test_nome_de_pessoa_sai_do_titulo(self):
        self.assertIn('Avaliação de desempenho', self.by_name)
        self.assertIn('Mudança de quarto', self.by_name)

    def test_rename_do_config(self):
        self.assertIn('Viagem de férias', self.by_name)

    def test_categoria_por_campo_e_por_titulo(self):
        self.assertEqual(self.by_name['Orçamento doméstico']['category'], 'financas')
        self.assertEqual(self.by_name['Clube do livro']['category'], 'lazer')
        self.assertEqual(self.by_name['Painel de metas']['category'], 'projetos')

    def test_faixas(self):
        for n in self.data['nodes']:
            self.assertTrue(0.3 <= n['weight'] <= 1.0)
            self.assertEqual(len(n['act']), len(self.data['weeks']))
            for c in n['connections']:
                self.assertTrue(0.14 <= c['proximity'] <= 1.0)

    def test_semanas(self):
        self.assertEqual(self.data['weeks'][0], '2026-07-13')
        self.assertEqual(len(self.data['weeks']), 14)
        self.assertEqual(self.data['until'], '2026-10-18')

    def test_atividade_conta_fatos_e_eventos_ate_until(self):
        import re
        title = 'Reforma do banheiro'
        vault = self.cfg['vault']['path']
        with open(os.path.join(vault, '50_Casa_Familia', title + '.md'), encoding='utf-8') as fh:
            facts = [d for d in re.findall(r'^- (\d{4}-\d{2}-\d{2})', fh.read(), re.M) if d <= '2026-10-18']
        with open(os.path.join(vault, '50_Casa_Familia', 'Eventos Casa.md'), encoding='utf-8') as fh:
            ev = re.findall(r'^- (\d{4}-\d{2}-\d{2}) \|.*\[\[' + title + r'\]\]', fh.read(), re.M)
        self.assertIn('2026-11-08', ev)   # o evento futuro existe no vault...
        expected = len(facts) + len([d for d in ev if d <= '2026-10-18'])
        self.assertEqual(sum(self.by_name[title]['act']), expected)   # ...mas não vira atividade

    def test_until_padrao_ignora_futuro(self):
        data, _, _ = build_graph.build(self.cfg, SOURCE, today=dt.date(2026, 10, 18))
        self.assertLessEqual(data['until'], '2026-10-18')

    def test_vazamento_de_nome_falha(self):
        cfg = _util.load_example(graph={'rename': {'Plano de carreira': 'Plano de carreira da Marta'}})
        data, _, notes = build_graph.build(cfg, SOURCE, until='2026-10-18')
        self.assertEqual(build_graph.person_hits(data, notes, cfg), ['marta'])

    def test_lista_extra_de_nomes(self):
        hits = build_graph.person_hits(self.data, self.notes, self.cfg, ['Corrida pela'])
        self.assertEqual(hits, ['corrida pela'])


class ConfigTest(unittest.TestCase):
    def test_lobo_invalido(self):
        with self.assertRaises(ConfigError):
            _util.load_example(categories={'x': {'label': 'X', 'color': '#FFFFFF', 'lobe': 'nariz'}})

    def test_pasta_para_categoria_inexistente(self):
        with self.assertRaises(ConfigError):
            _util.load_example(vault={'folders': {'10_Trabalho': 'nao_existe'}})

    def test_comentarios_somem(self):
        cfg = _util.load_example()
        self.assertNotIn('_comentario', cfg['categories'])
        self.assertNotIn('_folders', cfg['vault'])
        self.assertTrue(os.path.isabs(cfg['vault']['path']))

    def test_json_valido(self):
        with open(os.path.join(_util.EXAMPLES, 'sample_graph.json'), encoding='utf-8') as fh:
            self.assertIn('nodes', json.load(fh))


if __name__ == '__main__':
    unittest.main()
