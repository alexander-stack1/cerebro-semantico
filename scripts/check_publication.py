"""Varre o histórico textual sem imprimir dados encontrados."""
import argparse
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from redact import detect


# Correspondência do endereço COMPLETO, nunca por domínio ou prefixo.
ALLOWED_EMAILS = frozenset({
    '266852435+alexander-stack1@users.noreply.github.com',
    'noreply@github.com',
})
# Inclui pontuação válida na parte local e endereços com parte local entre aspas.
EMAIL = re.compile(
    r"""(?<![\w.!#$%&'*+/=?^`{|}~-])(?:[\w.!#$%&'*+/=?^`{|}~-]+|"(?:[^"\\]|\\.)+")"""
    r"""@(?:[\w-]+\.)+[A-Za-z][\w.-]*"""
)


def scan(text):
    """Preserva o resultado bruto e discrimina só os noreply conhecidos no conteúdo.

    E-mail pessoal aceito como autor é conferido nos metadados do Git, não removido
    do conteúdo. Outros dados continuam sujeitos aos detectores originais.
    """
    count = 0
    unknown_email = False

    def replace(match):
        nonlocal count, unknown_email
        address = match.group()
        # Aspas simples/backticks envolvendo um literal não pertencem ao endereço.
        if address[0] in ("'", '`') and text[match.end():match.end() + 1] == address[0]:
            address = address[1:]
            if address.startswith('@'):
                return match.group()  # literal de sufixo, sem parte local
        address = address.rstrip('.')  # pontuação terminal, nunca sufixo de domínio
        if address in ALLOWED_EMAILS:
            count += 1
            return '[EMAIL_AUTORIZADO]'
        unknown_email = True
        return match.group()

    filtered = EMAIL.sub(replace, text)
    blocking = detect(filtered)
    if unknown_email and 'email' not in blocking:
        blocking.append('email')
    return {'raw_findings': detect(text), 'allowed_email_occurrences': count,
            'blocking_findings': blocking}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('history', type=Path)
    result = scan(ap.parse_args().history.read_text(encoding='utf-8'))
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(bool(result['blocking_findings']))
