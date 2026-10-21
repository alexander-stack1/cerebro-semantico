# REPO_MAP: Cérebro Semântico

```
status: draft
generated_at: 2026-10-21
git_sha: sem commit (preencher após o primeiro commit)
generator: humano + Claude, revisão do mantenedor pendente
```

## Visão em uma frase

Lê um vault Markdown, calcula um grafo de temas com atividade semanal e injeta esse grafo numa página 3D de arquivo único.

## Módulos

| Módulo | Path | Responsabilidade | Entrypoint | Testes |
|---|---|---|---|---|
| Config | `pipeline/config.py` | Padrões, mescla e validação do JSON de config | `load()` | `tests/test_build_graph.py` (ConfigTest) |
| Vault | `pipeline/vault.py` | Frontmatter, wikilinks, fatos datados, linhas de evento | `read_notes()`, `read_event_rows()` | indireto |
| Grafo | `pipeline/build_graph.py` | Notas mantidas, arestas, latentes, peso, atividade, varredura de nomes | CLI e `build()` | `tests/test_build_graph.py` |
| Embed | `pipeline/embed_viewer.py` | Grava o grafo em `BRAIN_DATA`; versão sem esqueleto HTML | CLI, `embed()`, `strip_skeleton()` | `tests/test_embed_lint_timeline.py` |
| Redação | `pipeline/redact.py` | Troca e detecta dado pessoal e segredo | `redact()`, `detect()` | `tests/test_redact.py` |
| Mensagens | `pipeline/prep_messages.py` | NDJSON para extratos redigidos por segmento, aliases sigilosos | CLI e `Prep` | `tests/test_prep_messages.py` |
| Lint | `pipeline/lint_vault.py` | Sigilo (falha), estilo e links quebrados (aviso) | CLI e `lint()` | `tests/test_embed_lint_timeline.py` |
| Linha do tempo | `pipeline/timeline.py` | CSV de eventos e notas mensais, "Próximos" e índice | CLI e `build()` | `tests/test_embed_lint_timeline.py` |
| Briefing | `pipeline/briefing.template.md` | Instrução para o modelo que atualiza o vault | texto com placeholders | não |
| Viewer | `prototype/cerebro-semantico-3d.html` | Cérebro procedural, neurônios, sinapses, fótons, UI, linha do tempo | abrir no navegador; `window.CerebroSemantico` | `tools/visual/smoke.py` |
| Exemplo | `examples/` | Gerador do vault fictício, vault gerado, grafo de exemplo | `gerar_vault_exemplo.py` | testes de reprodução |
| Visual | `tools/visual/` | Smoke em Chromium SwiftShader e medição de luminância | `smoke.py`, `measure.py` | manual |
| Tamanho | `scripts/check_size.py` | Limite de 20.000 bytes no CI | CLI | CI |

## Fluxos críticos

1. Grafo: `config.load` → `vault.read_notes` → `build_graph.build` → `person_hits` → JSON.
2. Página: JSON → `embed_viewer.embed` → `prototype/...html` (seção 1. DADOS, constante `BRAIN_DATA`).
3. Mensagens: NDJSON → `prep_messages.Prep.run` (alias + `redact`) → `Prep.write` → extratos → modelo com briefing → vault → `lint_vault` → `timeline` → fluxo 1.

## Viewer por seções

O script do HTML tem 18 seções numeradas em comentários de bloco (busque `   N. TÍTULO`):

| Seção | Conteúdo |
|---|---|
| 1. DADOS | `MOCK_GRAPH`, `BRAIN_DATA`, `LATENT_THRESHOLD` |
| 2. CONFIGURAÇÃO GLOBAL | `CFG` |
| 3. GLSL COMPARTILHADO | ruído simplex; shaders de nó, sinapse, quads de brilho, poeira, nebulosa e casca do córtex |
| 4. UTILITÁRIOS | PRNG `mulberry32`, `normalizeData` (valida e simetriza o JSON), `createGlowQuads` |
| 5. CENA, CÂMERA, RENDERER E PÓS | composer com bloom; cérebro procedural (`LOBES`, `hemiShape`, `insideBrain`) |
| 6 a 8 | estado, construção do grafo (`buildGraph`, calor `heatAt`), descarte |
| 9. FÍSICA | molas de Hooke ancoradas no lobo (`stepPhysics`) |
| 10. ESTADOS VISUAIS | hover, seleção, foco por categoria, `brainFocus`, `updateLobeHeat`; linha do tempo (`setWeek`, `buildTimeline`, `togglePlay`) |
| 11. CÂMERA | voos com GSAP (`flyTo...`) |
| 12. DISPARO SINÁPTICO | onda de choque e partículas |
| 13. ATUALIZAÇÃO POR QUADRO | curvas, fótons, nós e rótulos |
| 14. RAYCAST | contra esferas analíticas |
| 15. UI | legenda, estatísticas, painel e busca |
| 16. EVENTOS | teclado, mouse, botões, troca de dados |
| 17. LAÇO PRINCIPAL | `tick` |
| 18. INICIALIZAÇÃO E API PÚBLICA | `window.CerebroSemantico` |

## Superfícies de alto risco (sempre esforço C)

- `pipeline/redact.py`, `pipeline/prep_messages.py`, `pipeline/lint_vault.py`
- `person_hits` e `clean_title` em `pipeline/build_graph.py`
- `.gitignore`, `config/`, `.github/workflows/`

## Como regenerar

Ver "Regenerar os artefatos de exemplo" no `CLAUDE.md`. Após o primeiro commit, preencher `git_sha` acima.

## NÃO VERIFICADO

- Comportamento em Windows (caminhos e encoding).
- Viewer em Safari e Firefox: só Chrome foi testado.
- Vault com YAML de várias linhas no frontmatter: o parser não suporta.
