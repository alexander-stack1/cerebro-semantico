import unittest

import _util  # noqa: F401  (ajusta sys.path)
from redact import detect, redact

# valores sintéticos, montados por concatenação para não parecerem dado real em buscas de segredo
CPF = '111.222.333' + '-44'
CNPJ = '11.222.333/0001' + '-81'
PROC = '0001234-56.2026' + '.5.01.0001'
CEL = '(21) 99876' + '-5432'
TOKEN = 'sk-' + 'a1B2c3D4e5F6g7H8i9J0'


class RedactTest(unittest.TestCase):
    def test_documentos(self):
        out = redact(f'cpf {CPF} cnpj {CNPJ} processo {PROC}')
        self.assertEqual(out, 'cpf [CPF] cnpj [CNPJ] processo [PROCESSO]')

    def test_contato(self):
        out = redact(f'liga no {CEL} ou escreve para fulana@exemplo.com.br')
        self.assertIn('[TEL]', out)
        self.assertIn('[EMAIL]', out)
        self.assertNotIn('9876', out)

    def test_url_guarda_so_o_dominio(self):
        self.assertEqual(redact('veja https://www.exemplo.com/a/b?c=1'), 'veja [URL:exemplo.com]')

    def test_cartao(self):
        self.assertEqual(redact('cartão 4111 1111 1111 1111'), 'cartão [NUM]')

    def test_credenciais(self):
        self.assertEqual(redact('senha: abacate123'), 'senha [REDACTED]')
        self.assertEqual(redact(f'chave {TOKEN}'), 'chave [REDACTED]')
        self.assertEqual(redact(f'usa {TOKEN} aqui'), 'usa [REDACTED] aqui')

    def test_quebra_de_linha(self):
        self.assertEqual(redact('a\nb'), 'a ⏎ b')

    def test_texto_comum_passa(self):
        self.assertEqual(redact('reunião às 15h na sala 3'), 'reunião às 15h na sala 3')


class DetectTest(unittest.TestCase):
    def test_detecta(self):
        self.assertEqual(detect(f'{CPF} {PROC} {CEL} a@b.com senha: abcdefgh12'),
                         ['CPF', 'processo', 'telefone', 'email', 'credencial'])

    def test_nota_limpa(self):
        self.assertEqual(detect('Fechou o orçamento em 3 parcelas.'), [])


if __name__ == '__main__':
    unittest.main()
