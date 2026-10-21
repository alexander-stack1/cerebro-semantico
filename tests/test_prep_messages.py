import json
import os
import unittest

import _util
import config as cfgmod
from prep_messages import Prep

CEL = '(21) 99876' + '-5432'


def msg(jid, name, text, me=False, sender='Alguém', ts='2026-10-01T13:05:00Z', **kw):
    r = {'chat_jid': jid, 'chat_name': name, 'from_me': me, 'sender_name': sender, 'sender_jid': '1@s',
         'text': text, 'timestamp': ts}
    r.update(kw)
    return json.dumps(r, ensure_ascii=False)


class PrepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = _util.TempDir()
        d = self.tmp.__enter__()
        _util.write_json(os.path.join(d, 'chat_map.json'), {
            'by_jid': {'equipe@g.us': {'dom': 'Profissional', 'sub': 'Equipe'},
                       'cliente1@s': {'dom': 'Profissional', 'sub': 'Clientes'},
                       'mae@s': {'dom': 'Pessoal', 'sub': 'Família'}},
            'by_name': {'Clube': {'dom': 'Lazer', 'sub': 'Amigos'}}})
        _util.write_json(os.path.join(d, 'aliases.json'), {'antigo@s': {'alias': 'Cliente-01', 'name': 'Cliente Antigo'}})
        path = _util.write_config(d, {'private': {'chat_map': 'chat_map.json', 'aliases': 'aliases.json',
                                                  'sensitive_names': None}})
        self.dir = d
        self.prep = Prep(cfgmod.load(path))

    def tearDown(self):
        self.tmp.__exit__()

    def run_prep(self, lines):
        out, n = self.prep.run(lines)
        report = self.prep.write(out, os.path.join(self.dir, 'x'))
        files = {}
        for f in os.listdir(os.path.join(self.dir, 'x')):
            with open(os.path.join(self.dir, 'x', f), encoding='utf-8') as fh:
                files[f[:-4]] = fh.read()
        return files, n, report

    def test_segmentos_redacao_e_fuso(self):
        files, n, _ = self.run_prep([
            msg('equipe@g.us', 'Equipe', f'me liga {CEL}', ts='2026-10-01T02:00:00Z'),
            msg('mae@s', 'Mãe', 'almoço domingo?', me=True),
            msg('x@s', 'Clube', 'jogo quinta'),
            msg('desconhecido@s', 'Loja', 'pedido saiu'),
        ])
        self.assertEqual(n, 4)
        self.assertEqual(sorted(files), ['N1_trabalho', 'N3_casa', 'N5_lazer', 'N9_outros'])
        self.assertIn('09-30 23:00 Alguém: me liga [TEL]', files['N1_trabalho'])   # UTC-3
        self.assertIn('EU: almoço domingo?', files['N3_casa'])
        self.assertIn('Não classificado / Revisar', files['N9_outros'])

    def test_sigilo_por_subcategoria_e_por_nome(self):
        files, _, _ = self.run_prep([
            msg('cliente1@s', 'Maria Cliente', 'sobre o contrato'),
            msg('novo@s', 'Dr. Fulano', 'segue o parecer'),
            msg('antigo@s', 'Cliente Antigo', 'obrigado'),
        ])
        txt = files['N0_sigiloso']
        self.assertNotIn('Maria', txt)
        self.assertNotIn('Fulano', txt)
        self.assertIn('Cliente-01', txt)
        self.assertIn('Novo-01', txt)
        self.assertIn('Novo-02', txt)
        self.assertIn('ELE: obrigado', txt)
        with open(os.path.join(self.dir, 'aliases.json'), encoding='utf-8') as fh:
            keys = json.load(fh)
        self.assertEqual(len(keys), 3)   # aliases novos ficam gravados para a próxima rodada

    def test_midia_sem_texto_e_audio_transcrito(self):
        files, _, _ = self.run_prep([
            msg('mae@s', 'Mãe', 'sent image'),
            msg('mae@s', 'Mãe', 'sent audio', transcript='chego às sete'),
        ])
        self.assertNotIn('sent image', files['N3_casa'])
        self.assertIn('[áudio] chego às sete', files['N3_casa'])

    def test_amostra_de_grupo_grande(self):
        lines = [msg('equipe@g.us', 'Equipe', f'mensagem longa número {i} ' + 'x' * 80, ts=f'2026-10-01T10:{i % 60:02d}:00Z')
                 for i in range(450)]
        lines.append(msg('equipe@g.us', 'Equipe', 'minha', me=True))
        files, _, _ = self.run_prep(lines)
        body = files['N1_trabalho'].strip().split('\n')[1:]
        self.assertEqual(len(body), 151)   # 150 dos outros + 1 do dono
        self.assertTrue(any(' EU: minha' in x for x in body))

    def test_jid_nunca_aparece_no_extrato(self):
        num_a, num_b = '5521' + '998765432', '5521' + '987654321'
        files, _, _ = self.run_prep([
            msg(num_a + '@s.whatsapp.net', None, 'oi', sender=None, sender_jid=num_a + '@s.whatsapp.net'),
            msg(num_b + '@s.whatsapp.net', None, 'tudo bem', sender=None, sender_jid=num_b + '@s.whatsapp.net'),
        ])
        txt = files['N9_outros']
        self.assertNotIn('98765432', txt)
        self.assertNotIn('87654321', txt)
        self.assertNotIn('@s.whatsapp', txt)
        self.assertIn('?: oi', txt)
        self.assertEqual(txt.count('===== CONVERSA: [sem nome]'), 2)   # conversas sem nome não se fundem

    def test_nome_de_remetente_e_de_conversa_passam_por_redacao(self):
        files, _, _ = self.run_prep([
            msg('equipe@g.us', 'Equipe', 'bom dia', sender='+55 ' + CEL),
            msg('loja@s', 'Loja ' + CEL, 'pedido saiu'),
        ])
        self.assertNotIn('5432', files['N1_trabalho'] + files['N9_outros'])
        self.assertIn('[TEL]: bom dia', files['N1_trabalho'])
        self.assertIn('CONVERSA: Loja [TEL]', files['N9_outros'])


if __name__ == '__main__':
    unittest.main()
