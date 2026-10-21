import csv
import json
import os
import re
import shutil
import unittest

import _util
import embed_viewer
import lint_vault
import timeline

PROTO = os.path.join(_util.ROOT, 'prototype', 'cerebro-semantico-3d.html')


class EmbedTest(unittest.TestCase):
    def setUp(self):
        with open(PROTO, encoding='utf-8') as fh:
            self.page = fh.read()

    def test_prototipo_traz_o_grafo_de_exemplo(self):
        m = re.search(r'const BRAIN_DATA = (.*);\n', self.page)
        with open(os.path.join(_util.EXAMPLES, 'sample_graph.json'), encoding='utf-8') as fh:
            self.assertEqual(json.loads(m.group(1).replace('<\\/', '</')), json.load(fh))

    def test_troca_dados_e_escapa_script(self):
        page = embed_viewer.embed(self.page, {'categories': {}, 'nodes': [], 'source': '</script>'})
        self.assertIn('const BRAIN_DATA = {"categories":{},"nodes":[],"source":"<\\/script>"};\n', page)
        self.assertEqual(page.count('const BRAIN_DATA = '), 1)

    def test_sem_esqueleto(self):
        bare = embed_viewer.strip_skeleton(self.page)
        self.assertTrue(bare.startswith('<title>'))
        self.assertIsNone(re.search(r'<(html|body|head)[\s>]', bare))
        self.assertNotIn('<!doctype', bare.lower())


class LintTest(unittest.TestCase):
    def test_vault_de_exemplo_passa(self):
        cfg = _util.load_example()
        _files, issues, _broken, critical = lint_vault.lint(cfg['vault']['path'], cfg)
        self.assertEqual(critical, 0, dict(issues))

    def test_acusa_dado_sigiloso_e_estilo(self):
        cfg = _util.load_example()
        with _util.TempDir() as tmp:
            with open(os.path.join(tmp, 'Nota.md'), 'w', encoding='utf-8') as fh:
                fh.write('# Nota\n\nCPF 111.222.333' + '-44 \u2014 em suma, [[Inexistente]].\n')
            with open(os.path.join(tmp, 'nomes.txt'), 'w', encoding='utf-8') as fh:
                fh.write('# comentário\nFulana de Tal\n')
            with open(os.path.join(tmp, 'Outra.md'), 'w', encoding='utf-8') as fh:
                fh.write('Conversa com fulana de tal.\n')
            cfg['private']['sensitive_names'] = os.path.join(tmp, 'nomes.txt')
            _files, issues, broken, critical = lint_vault.lint(tmp, cfg)
        self.assertEqual(critical, 2)
        self.assertIn('SIGILO CPF', issues)
        self.assertIn('SIGILO nome de contato sigiloso', issues)
        self.assertIn('travessão', issues)
        self.assertIn('frase IA:em suma', issues)
        self.assertIn('Inexistente', broken)


class TimelineTest(unittest.TestCase):
    def test_gera_meses_futuro_e_csv(self):
        cfg = _util.load_example()
        with _util.TempDir() as tmp:
            vault = os.path.join(tmp, 'v')
            shutil.copytree(cfg['vault']['path'], vault)
            csv_path = os.path.join(tmp, 'eventos.csv')
            st = timeline.build(vault, cfg, csv_path, '2026-10-18')
            folder = os.path.join(vault, '90_Linha_do_tempo')
            files = sorted(os.listdir(folder))
            with open(os.path.join(folder, 'Linha do tempo Próximos.md'), encoding='utf-8') as fh:
                fut = fh.read()
            with open(csv_path, encoding='utf-8') as fh:
                rows = list(csv.reader(fh))
            with open(os.path.join(folder, 'Linha do tempo.md'), encoding='utf-8') as fh:
                idx = fh.read()
        self.assertEqual(st['months'], ['2026-07', '2026-08', '2026-09', '2026-10'])
        self.assertIn('Linha do tempo Outubro 2026.md', files)
        self.assertEqual(st['future'], 2)
        self.assertIn('[[Reforma do banheiro]]', fut)
        self.assertEqual(len(rows) - 1, st['events'])
        self.assertIn('| Mês | Profissional | Pessoal | Lazer | Viagens | Financeiro | Total |', idx)
        self.assertIn('que o vault de exemplo comprova', idx)


if __name__ == '__main__':
    unittest.main()
