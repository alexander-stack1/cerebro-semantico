# CLAUDE.md: Cérebro Semântico

Contrato deste repositório para agentes de código (vale também como AGENTS.md).

## Entrada

1. Se existir `CLAUDE.local.md` na raiz, leia primeiro. São as regras pessoais do mantenedor. Fica fora do git.
2. Este arquivo é o contrato do repo.
3. Estado atual, histórico e próximos passos: `docs/HANDOFF.md`.
4. Mapa operacional: `docs/agent/REPO_MAP.md` (confira o SHA do cabeçalho).
5. Decisões estáveis: `docs/agent/DECISIONS.md`.

Memória de chat não autoriza caminho nem fato. Cite o arquivo.

## Stack real

- Pipeline: Python 3.9+, só biblioteca padrão. Sem `requirements.txt` de propósito (ADR-001).
- Viewer: HTML de arquivo único, Three.js r160 e GSAP 3.12.5 via importmap do jsDelivr, GLSL próprio.
- Testes: `python3 -m unittest discover -s tests` (59 testes).
- Tamanho: `python3 scripts/check_size.py` (20.000 bytes por arquivo de texto).
- Visual (opcional, precisa de playwright, pillow e numpy): `python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html`.
- Rodar local: abrir `prototype/cerebro-semantico-3d.html` no navegador.

## Esforço S / M / C

Primeira linha de toda resposta de implementação: `Esforço: S|M|C | motivo: ... | Repo: cerebro-semantico @ <git rev-parse --short HEAD>`.

Força C (modo fail-closed: evidência, escopo fixo, TDD, dado sensível como [REDACTED]) se tocar:

- `pipeline/redact.py`, `pipeline/prep_messages.py`, `pipeline/lint_vault.py`
- a varredura de nomes em `pipeline/build_graph.py` (`person_hits`, `clean_title`)
- `.gitignore`, `config/`, qualquer leitura de `private/`
- `.github/workflows/` e qualquer passo de publicação ou release
- `docs/PRIVACIDADE.md`

## Onde mexer

| Quero... | Começar em |
|---|---|
| Regra de peso, proximidade ou latente | `pipeline/build_graph.py` (`build`) |
| Categoria de uma nota | `pipeline/build_graph.py` (`category_of`) e `config/config.example.json` |
| Leitura do vault (frontmatter, links, datas) | `pipeline/vault.py` |
| Novo padrão de redação | `pipeline/redact.py` + `tests/test_redact.py` |
| Segmentos de mensagens | `pipeline/prep_messages.py` (`segment_of`) |
| Visual do cérebro, shaders, interação | `prototype/cerebro-semantico-3d.html` (seções numeradas no comentário do topo) |
| Dados de exemplo | `examples/gerar_vault_exemplo.py`, depois regenere `examples/sample_graph.json` e o protótipo |

## Não fazer neste repo

- Commitar dado real: exportação de mensagens, vault real, `chat_map.json`, `aliases.json`, `config/config.json`, grafo real. O `.gitignore` bloqueia; não force com `git add -f`.
- Colar nome de pessoa real, telefone, e-mail ou trecho de conversa em issue, commit, teste ou doc. Teste usa valor sintético montado por concatenação.
- Mudar `examples/vault` à mão. Mude o gerador e regenere.
- Mudar o viewer sem regenerar o protótipo pelo `embed_viewer.py` e sem rodar o smoke visual.
- Declarar defeito visual por impressão. Meça com `tools/visual/measure.py` em tamanho real (1440x900).
- Arquivo de texto acima de 20.000 bytes sem exceção justificada em `.agent-size-ignore`.
- `git commit --no-verify`.
- Afirmar "pronto" sem o comando de verificação do nível S/M/C.

## Regenerar os artefatos de exemplo

```bash
python3 examples/gerar_vault_exemplo.py
python3 pipeline/build_graph.py --config config/config.example.json --out examples/sample_graph.json \
    --source "Vault de exemplo · 13/07 a 18/10/2026" --until 2026-10-18
python3 pipeline/embed_viewer.py --template prototype/cerebro-semantico-3d.html \
    --json examples/sample_graph.json --out prototype/cerebro-semantico-3d.html
```

Os testes `test_sample_graph_reproduz`, `test_vault_de_exemplo_reproduz` e `test_prototipo_traz_o_grafo_de_exemplo` falham se um desses passos for esquecido.

## Verificação mínima

| Classe | Comando |
|---|---|
| S | `python3 -m unittest discover -s tests` |
| M | S + `python3 scripts/check_size.py` + smoke visual se tocou o viewer |
| C | M + teste novo que falha antes da mudança + revisão do diff procurando dado real |

## Estilo

Português do Brasil. Frase curta, voz ativa. Sem travessão. Commits em Conventional Commits.
