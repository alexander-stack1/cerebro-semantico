# HANDOFF

Estado em 2026-10-21. Escrito para a próxima sessão de agente (Claude Code) e para quem chega ao projeto.

## Origem

O projeto nasceu numa sessão do Claude, de 2026-10-15 a 2026-10-21, como visualização 3D de um vault pessoal montado a partir de conversas de WhatsApp. O vault, as conversas e o grafo real não estão neste repositório. Ficam na máquina do mantenedor.

Etapas da sessão de origem:

1. Grafo semântico 3D com nós, sinapses Catmull-Rom e fótons, a partir de dados de exemplo.
2. Cérebro anatômico procedural: hemisférios com giros, fissura, cerebelo, casca de vidro com fresnel, neurônios de fundo e fibras com pulsos. Cada categoria ocupa um lobo.
3. Correção da tela preta no centro em GPU real: NaN de `pow` com base negativa, espalhado pelo bloom (ADR-007).
4. Calor por atividade e recência, linha do tempo semanal com play, rótulos truncados com colisão.
5. Generalização para código aberto (esta entrega): pipeline por config, vault e grafo fictícios, testes, docs.

## Estado atual

| Parte | Estado |
|---|---|
| Pipeline (`pipeline/`) | Completo para o fluxo atual. Saída idêntica ao pipeline de origem (ADR-010). |
| Testes (`tests/`) | 62 testes, só biblioteca padrão, rodam em menos de 1 segundo. |
| Exemplo (`examples/`) | Vault fictício de 59 arquivos, 40 temas em 8 categorias, 14 semanas. Grafo de 74 sinapses diretas e 5 latentes. |
| Viewer (`prototype/`) | Funciona. Arquivo único de 127 KB, acima do limite de 20 KB (exceção em `.agent-size-ignore`). |
| CI (`.github/workflows/ci.yml`) | Testes em Python 3.9 e 3.12 e limite de tamanho, no runner `ubuntu-24.04` (a imagem 26.04 não tem 3.9). Movido na fase 1, em 2026-10-21. |

| Demonstrações (`docs/media/`) | Três capturas e dois vídeos do exemplo, com manifesto de origem e prévias GIF. Roteiros e verificação em `docs/DEMONSTRACOES.md`. |

## Como foi verificado

- Equivalência byte a byte com o pipeline de origem sobre o vault real (173 temas, 723 conexões diretas e 86 latentes): grafo com e sem `--until`, página local e versão sem esqueleto (igual à página publicada), lint, linha do tempo (CSV e notas) e extratos com aliases, em duas exportações de mensagens diferentes.
- Smoke visual em Chromium SwiftShader, 1440x900, com o vault de exemplo: sem erro de página; visão geral com 0,7% de pixels saturados na caixa central.
- Na sessão de origem, o viewer com o grafo real rodou a 57 a 60 fps no Chrome do mantenedor, numa GPU real.

## Problemas conhecidos

1. **Saturação no estado ativo, dependente do nó.** SwiftShader, 1440x900, caixa central: ativar "Reforma do banheiro" deu 9,7% de pixels saturados; "Alimentação da semana" deu 2,5%; o grafo real, 3,2%. A câmera entra no córtex perto do centro. NÃO VERIFICADO em GPU real.
2. **FPS perto de 1 no SwiftShader.** Animação e física andam devagar no teste headless. Espere mais antes de julgar um estado.
3. **Depende de CDN.** Sem internet a página não carrega Three.js e GSAP.
4. **Frontmatter simples.** Só `chave: valor` numa linha. Lista YAML de várias linhas não é lida.
5. **Varredura de nomes só pega tokens de 4 letras ou mais.** Um nome curto (ex.: "Rui") passa pela varredura. `clean_title` tira o nome do título quando a pessoa tem nota própria; use também `private/sensitive_names.txt`.
6. **Redação só cobre formatos do Brasil.**
7. **NDJSON de mensagens com esquema fixo.** Campos listados no topo de `pipeline/prep_messages.py`. Outro exportador precisa de adaptador.
8. **Textos fixos em português** na linha do tempo e no viewer.

## Publicação: privado primeiro, aberto depois

Decisão do mantenedor em 2026-10-21 (ADR-011): o repositório fica na conta pessoal do GitHub (`alexander-stack1`), começa **privado** e só vira público quando o mantenedor disser que está ok. Esforço C nas duas fases: publicar é a superfície de maior risco de vazamento deste projeto.

### Fase 1: criar o repositório privado

Peça ao Claude Code: "Faça a fase 1 da publicação do docs/HANDOFF.md."

1. Confirmar a conta: `gh api user -q .login` precisa responder `alexander-stack1`. Se responder outra conta, pare e pergunte.
2. E-mail dos commits: o e-mail global do git do mantenedor é pessoal e ficaria público no histórico. Configure só neste repo o e-mail noreply do GitHub, antes do primeiro commit: `git config user.email "$(gh api user -q .id)+$(gh api user -q .login)@users.noreply.github.com"`. Confira com `git config user.email`.
3. Mover o CI para o lugar: `mkdir -p .github/workflows && mv docs/ci-workflow.yml .github/workflows/ci.yml && git add -A`. Feito em 2026-10-21.
4. Conferir que nada privado está no stage:
   - `git status --short --ignored` mostra `CLAUDE.local.md` como ignorado (`!!`);
   - `git ls-files | grep -iE 'ndjson|chat_map|aliases|chaves|config\.json$|\.zip$'` não imprime nada.
5. Rodar `python3 -m unittest discover -s tests` e `python3 scripts/check_size.py`. Os dois precisam passar.
6. Primeiro commit, com o hook ativo e sem `--no-verify`: `git commit -m "feat: versão inicial do cérebro semântico"`.
7. Criar o remoto privado e enviar: `gh repo create alexander-stack1/cerebro-semantico --private --source . --remote origin --push`.
8. Provar a visibilidade: `gh repo view alexander-stack1/cerebro-semantico --json visibility -q .visibility` responde `PRIVATE`.
9. Conferir o CI: `gh run list --limit 1` termina em `success`. Se falhar, corrigir antes de qualquer outro passo.
10. Preencher `git_sha` em `docs/agent/REPO_MAP.md` e commitar. Propor ao mantenedor a linha do repo em `_CAMINHOS.md`, com o remoto; não editar sem ok.

### Fase 2: abrir o repositório (só com ok explícito do mantenedor)

Peça ao Claude Code: "Faça o checklist da fase 2 do docs/HANDOFF.md e me mostre o resultado. Não mude a visibilidade." Cada item precisa de evidência (comando e saída), não de impressão.

1. Licença decidida: MIT, por decisão do mantenedor em 2026-10-21 (ADR-012). Conferir que `LICENSE` começa com `MIT License`.
2. Varredura do histórico inteiro, não só do HEAD. Preserve o resultado bruto e discrimine somente os dois endereços noreply completos autorizados em `scripts/check_publication.py`:
   ```bash
   export HISTORICO_PUBLICACAO="$(mktemp -t cerebro-historico.XXXXXX)"
   git log -p --all --format='%H%n%B' -- . ':!tests' > "$HISTORICO_PUBLICACAO" &&
   python3 scripts/check_publication.py "$HISTORICO_PUBLICACAO"
   ```
   Resultado esperado: `blocking_findings: []` e saída 0. `raw_findings` pode conter `email`; `allowed_email_occurrences` conta as ocorrências exatas autorizadas. Outros endereços, inclusive de outras contas noreply, bloqueiam. O e-mail pessoal aceito como autor não ganha exceção no conteúdo. Não excluir por domínio genérico.
   Inspecione separadamente todas as versões históricas de `tests/`, classificando valores sintéticos por arquivo e versão. Confira também os blobs completos de cada commit, pois diffs de merge podem omitir conteúdo.
3. Varredura de nomes sigilosos do mantenedor no mesmo histórico. O comando está no `CLAUDE.local.md` e lê `HISTORICO_PUBLICACAO`. Incluir todos os nomes completos, sem excluir os curtos. Imprime só a contagem, nunca os nomes. Resultado esperado: `0`.
4. Nenhum caminho da máquina do mantenedor no histórico: `grep -cE '/U[s]ers/|analise-w[h]atsapp' "$HISTORICO_PUBLICACAO"` responde `0`.
5. E-mails de autor e committer conhecidos: `git log --all --format='%ae%n%ce' | sort -u` lista só o noreply da conta (`users.noreply.github.com`), `noreply@github.com` (committer dos merges feitos pelo GitHub) e o e-mail pessoal do mantenedor, que o squash merge grava como autor. O mantenedor aceitou esse e-mail em 2026-10-21 porque ele já é público. Qualquer outro endereço bloqueia a abertura.
6. `examples/` só com conteúdo fictício. Rodar `python3 tools/visual/preview.py --check --verify-ci`: confere o run concluído e o artefato do GitHub byte a byte, além dos hashes de `docs/img/preview.png`, do grafo e das fontes registradas em `docs/img/preview-origin.json`. Para regenerar, `python3 tools/visual/preview.py` verifica a reprodução do vault/grafo, captura o HTML de exemplo em Chromium e grava o PNG sem conversão. Requer as dependências opcionais do smoke. O job `preview` do CI também gera a captura e oferece o artefato para download. Inspecione a imagem. A animação varia entre execuções; reproduz-se o procedimento, sem prometer pixels idênticos.
   Para as mídias da galeria, execute também `python3 tools/visual/animated_preview.py --check` e `python3 tools/visual/demo_media.py --verify-ci` e inspecione os três PNGs e os dois vídeos. Ver `docs/DEMONSTRACOES.md`.
7. CI verde no último commit.
8. Remover apenas o temporário criado nesta execução: `rm -f -- "$HISTORICO_PUBLICACAO"; unset HISTORICO_PUBLICACAO`. Fazer isso também em caso de falha, antes de encerrar.
9. Mostrar o resultado ao mantenedor e esperar o ok. Só então: `gh repo edit alexander-stack1/cerebro-semantico --visibility public --accept-visibility-change-consequences`, e conferir com o comando do passo 8 da fase 1 (`PUBLIC`).

Se qualquer item falhar, o repositório continua privado. Dado sensível achado no histórico não se resolve com um commit novo: o histórico precisa ser reescrito antes de abrir, com decisão do mantenedor.

## Roadmap sugerido (em ordem)

1. **Modularizar o viewer.** Meta: arquivos de até 20 KB por responsabilidade (dados, GLSL, cérebro, grafo, física, câmera, UI, laço) e a mesma página única como produto de build. Duas opções, a decidir com o mantenedor:
   - (a) módulos ES nativos em `src/` e um script Python que junta tudo num HTML. Mantém zero dependência.
   - (b) Vite. Traz `node_modules`, servidor de desenvolvimento e build pronto.
   Aceite: smoke sem erro, medição da visão geral e do estado ativo dentro de 1 ponto percentual da versão atual, testes verdes, exceção removida do `.agent-size-ignore`.
2. **Carregar dados sem embed**: arrastar um JSON para a página, ou `?data=URL`.
3. **Modo offline**: opção de embutir Three.js e GSAP.
4. **Corrigir o problema conhecido 1** com medição antes e depois.
5. **Rótulos de lobo no córtex** e legenda que mostra o lobo de cada categoria.
6. **Resumo da nota no painel** (primeira frase da nota, gerada pelo pipeline).
7. **Qualidade automática**: reduzir neurônios de fundo e bloom quando o FPS cair.
8. **Deep link**: `#n=<id>&w=<semana>`.
9. **CLI única** (`cerebro build`, `cerebro embed`) com `pyproject.toml`.
10. **Conexões semânticas por embeddings**, locais e opcionais.
11. **Interface em inglês.**

## Primeira sessão no Claude Code

1. Ler `CLAUDE.md`, `CLAUDE.local.md` (se existir), este arquivo, `docs/agent/REPO_MAP.md` e `docs/agent/DECISIONS.md`.
2. Rodar `python3 -m unittest discover -s tests` e `python3 scripts/check_size.py`.
3. Abrir `prototype/cerebro-semantico-3d.html` no navegador.
4. Fazer a fase 1 da publicação (seção acima). Confirmar com o mantenedor, antes do roadmap, a opção (a) ou (b) do item 1.
5. Depois do primeiro commit, preencher `git_sha` em `docs/agent/REPO_MAP.md`. Feito: `f6b5054`.
