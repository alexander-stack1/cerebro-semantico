"""A publicação tolera só os e-mails completos explicitamente autorizados."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

import _util
sys.path.insert(0, str(pathlib.Path(_util.ROOT) / 'scripts'))
from check_publication import scan


class PublicationTest(unittest.TestCase):
    def test_noreply_conhecido_nao_bloqueia(self):
        result = scan('autor: noreply' + '@github.com')
        self.assertEqual(result['raw_findings'], ['email'])
        self.assertEqual(result['allowed_email_occurrences'], 1)
        self.assertEqual(result['blocking_findings'], [])

    def test_enderecos_parecidos_continuam_bloqueados(self):
        for address in ('noreply' + '@github.com.evil.test',
                        'outro+noreply' + '@github.com',
                        'outra-conta' + '@users.noreply.github.com'):
            with self.subTest(address=address):
                self.assertIn('email', scan(address)['blocking_findings'])

    def test_pontuacao_e_caixa_nao_burlam_lista(self):
        for address in ('outro!noreply' + '@github.com',
                        "outro'noreply" + '@github.com',
                        'outra-conta' + '@users.NOREPLY.GITHUB.COM'):
            with self.subTest(address=address):
                result = scan(address)
                self.assertEqual(result['allowed_email_occurrences'], 0)
                self.assertIn('email', result['blocking_findings'])

    def test_delimitadores_de_codigo_preservam_endereco_completo(self):
        for quote in ("'", '"', '`'):
            result = scan(quote + 'noreply' + '@github.com' + quote)
            self.assertEqual(result['allowed_email_occurrences'], 1)
            self.assertEqual(result['blocking_findings'], [])

    def test_noreply_nao_oculta_outros_dados(self):
        text = 'noreply' + '@github.com senha: ' + 'abcdefgh12'
        self.assertIn('credencial', scan(text)['blocking_findings'])

    def test_sufixo_de_jid_sem_parte_local_nao_e_email(self):
        result = scan("endswith('" + '@g.us' + "')")
        self.assertEqual(result['allowed_email_occurrences'], 0)
        self.assertEqual(result['blocking_findings'], [])

    def test_cli_falha_sem_imprimir_valor(self):
        sentinel = 'pessoa' + '@secreto.test'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
            f.write(sentinel); f.flush()
            p = subprocess.run([sys.executable, str(pathlib.Path(_util.ROOT) / 'scripts/check_publication.py'), f.name],
                               capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertNotIn(sentinel, p.stdout + p.stderr)
