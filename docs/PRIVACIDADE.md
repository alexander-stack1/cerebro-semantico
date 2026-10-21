# Privacidade

O Cérebro Semântico nasceu para olhar conversas e notas pessoais. Este documento diz o que fica onde e o que o código garante. Leia antes de usar com dados reais.

## Regras do projeto

1. Nenhum dado pessoal entra no repositório. O `.gitignore` bloqueia `private/`, `config/config.json`, `*.ndjson`, `chat_map.json`, `aliases.json`, `extratos/` e `out/`.
2. O grafo publicado tem só temas. Notas de pessoas ficam de fora. Nome de pessoa é tirado dos títulos. O build falha se um nome sobrar.
3. Texto de mensagem nunca entra no grafo. O grafo tem título, categoria, peso, conexões e contagens por semana.
4. Antes de um texto sair do computador para um modelo de linguagem, ele passa por `redact()`.
5. Conversa sigilosa (por exemplo, cliente de um profissional com dever de sigilo) vira alias estável (`Cliente-01`, `Novo-03`). O nome real fica só em `private/aliases.json`.
6. O lint do vault falha se uma nota gravada tiver CPF, número de processo, telefone, e-mail, credencial ou nome de contato sigiloso.

## Onde cada dado fica

| Dado | Onde | Versionado |
|---|---|---|
| Exportação de mensagens (NDJSON) | máquina do dono | não |
| Classificação de conversas (`chat_map.json`) | `private/` | não |
| Aliases e nomes reais (`aliases.json`) | `private/` | não |
| Lista extra de nomes proibidos (`sensitive_names.txt`) | `private/` | não |
| Extratos redigidos | `extratos/` | não |
| Vault de notas | onde o dono quiser | não |
| Grafo JSON e página gerada | `out/` | não |
| Vault e grafo de exemplo | `examples/` | sim, conteúdo fictício |

## O que a redação cobre

`pipeline/redact.py` troca: CPF, CNPJ, número de processo no padrão CNJ, telefone com DDD, e-mail, URL (guarda só o domínio), sequência de 13 a 19 dígitos (cartão, conta), palavra-chave seguida de valor (`senha`, `token`, `chave`, `api key`, `secret`, `código`) e formatos conhecidos de token (`sk-`, `gh*_`, `AKIA`, `EAA`).

## O que a redação não cobre

- Nome de pessoa dentro do texto. Use alias por conversa e a lista `sensitive_names.txt`.
- Endereço, placa, data de nascimento e dado de saúde escrito por extenso.
- Dado em imagem, PDF ou áudio sem transcrição.
- Formatos de outros países.

Redação é rede de segurança. A proteção principal é não mandar ao modelo o que ele não precisa ler, e revisar o vault antes de publicar.

## Publicação

A página gerada embute o grafo inteiro. Quem abre a página vê todos os títulos de tema. Revise os títulos antes de compartilhar. Ao publicar num host, prefira link privado.

## Como reportar um vazamento

Abra uma issue sem colar o dado. Descreva o tipo (por exemplo, "telefone com DDI passou pela redação") e um exemplo sintético.
