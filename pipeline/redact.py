"""Redação e detecção de dados pessoais e segredos em texto livre.

redact(texto)  troca o dado por um marcador ([CPF], [TEL], [REDACTED]...). Usada antes de
               qualquer texto de mensagem sair do computador do dono para um modelo de linguagem.
detect(texto)  devolve os tipos de dado sensível encontrados. Usada pelo lint do vault, que
               falha se uma nota gravada tiver CPF, processo, telefone, e-mail ou credencial.

Os padrões são do Brasil (CPF, CNPJ, número CNJ de processo, celular com DDD).
Redação é uma rede de segurança, não uma garantia: ver docs/PRIVACIDADE.md.
"""
import re

# ordem importa: CPF e CNPJ antes de telefone; cartão antes de credencial
REDACTIONS = [
    ('CPF', re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    ('CNPJ', re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'), '[CNPJ]'),
    ('PROCESSO', re.compile(r'\b\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}\b'), '[PROCESSO]'),
    ('TEL', re.compile(r'(?<!\d)(\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}(?!\d)'), '[TEL]'),
    ('EMAIL', re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), '[EMAIL]'),
    ('URL', re.compile(r'https?://([^/\s]+)\S*'), lambda m: '[URL:' + m.group(1).replace('www.', '') + ']'),
    ('NUM', re.compile(r'\b(?:\d[ -]?){13,19}\b'), '[NUM]'),
    ('CREDENCIAL', re.compile(r'(?i)\b(senha|password|c[oó]digo|token|chave|api[_ ]?key|secret)\s*(?:é|:|=)?\s*\S+'),
     lambda m: m.group(1) + ' [REDACTED]'),
    ('TOKEN', re.compile(r'\b(EAA[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b'),
     '[REDACTED]'),
]

# detecção em nota já escrita: formatos estritos, para não acusar número qualquer
DETECTORS = {
    'CPF': re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'),
    'processo': re.compile(r'\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b'),
    'telefone': re.compile(r'\(?\b\d{2}\)?\s?9\d{4}[-\s]?\d{4}\b'),
    'email': re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}'),
    'credencial': re.compile(r'(?i)(senha|token|api[_ ]?key|secret)\s*(?:é|:|=)\s*[A-Za-z0-9_\-]{8,}'
                             r'|\b(EAA[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{16,})'),
}


def redact(text, newline=' ⏎ '):
    """Aplica todas as redações. Quebras de linha viram o marcador newline (uma mensagem, uma linha)."""
    for _name, rx, rep in REDACTIONS:
        text = rx.sub(rep, text)
    return text.replace('\n', newline) if newline is not None else text


def detect(text):
    """Tipos de dado sensível presentes no texto, em ordem estável."""
    return [k for k, rx in DETECTORS.items() if rx.search(text)]
