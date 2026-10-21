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
EMAIL = re.compile(r'(?<![\w.+-])[\w.+-]+@(?:[\w-]+\.)+[A-Za-z]{2,}(?![\w.-])')


def scan(text):
    """Preserva o resultado bruto e discrimina só os noreply conhecidos no conteúdo.

    E-mail pessoal aceito como autor é conferido nos metadados do Git, não removido
    do conteúdo. Outros dados continuam sujeitos aos detectores originais.
    """
    count = 0

    def replace(match):
        nonlocal count
        if match.group() in ALLOWED_EMAILS:
            count += 1
            return '[EMAIL_AUTORIZADO]'
        return match.group()

    filtered = EMAIL.sub(replace, text)
    return {'raw_findings': detect(text), 'allowed_email_occurrences': count,
            'blocking_findings': detect(filtered)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('history', type=Path)
    result = scan(ap.parse_args().history.read_text(encoding='utf-8'))
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(bool(result['blocking_findings']))
