# DECISIONS: Cérebro Semântico

ADRs curtos. Só o que muda o próximo diff.

### ADR-001: Pipeline só com biblioteca padrão

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O pipeline roda em máquina pessoal, às vezes agendado, com dado sensível.
- **Decisão:** Python 3.9+ sem dependência externa. Playwright, Pillow e numpy só em `tools/visual/`, opcionais.
- **Consequência:** Não adicionar pacote ao pipeline sem ADR novo. JSON no lugar de YAML no config.
- **Paths:** `pipeline/`, `config/`

### ADR-002: Tudo que é pessoal vem do config

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O código nasceu com categorias, pastas e nomes de um vault real dentro dos scripts.
- **Decisão:** Categorias, pastas, regras de categoria, renomeações, segmentos de mensagens, frases proibidas e textos da linha do tempo ficam no JSON de config. O código não tem nome, pasta ou categoria de ninguém.
- **Consequência:** Regra nova entra como chave de config com padrão em `DEFAULTS` e validação em `config.validate`.
- **Paths:** `pipeline/config.py`, `config/config.example.json`

### ADR-003: O grafo publicado só tem temas

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** A página embute o grafo inteiro e pode ser compartilhada.
- **Decisão:** Notas de pessoa ficam fora. Nome de pessoa sai do título (`clean_title`) ou é trocado por `graph.rename`. `build_graph.py` sai com código 1 se um token de nome sobrar.
- **Consequência:** Nunca baixar a régua da varredura para fazer o build passar. Corrigir com `rename` ou `person_scan_allow` justificado.
- **Paths:** `pipeline/build_graph.py`

### ADR-004: Redação antes de qualquer texto sair da máquina

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** Extratos de mensagens vão para um modelo de linguagem.
- **Decisão:** Todo texto passa por `redact()`. Conversa sigilosa vira alias estável gravado em `private/aliases.json`. O lint do vault falha com dado sigiloso.
- **Consequência:** Padrão novo de dado pessoal entra com teste em `tests/test_redact.py`, valor sintético montado por concatenação.
- **Paths:** `pipeline/redact.py`, `pipeline/prep_messages.py`, `pipeline/lint_vault.py`

### ADR-005: Viewer em arquivo único, com exceção de tamanho temporária

- **Data:** 2026-10-21
- **Status:** accepted (temporário)
- **Contexto:** O protótipo tem cerca de 127 KB e precisa abrir com duplo clique e ser publicável como página única.
- **Decisão:** `prototype/cerebro-semantico-3d.html` fica em `.agent-size-ignore` até a modularização (roadmap item 1 em `docs/HANDOFF.md`).
- **Consequência:** A modularização precisa manter a saída de arquivo único como produto de build.
- **Paths:** `prototype/`, `.agent-size-ignore`

### ADR-006: Three.js r160 e GSAP 3.12.5 fixos via importmap

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** Sem bundler, as bibliotecas vêm do jsDelivr.
- **Decisão:** Versões exatas no importmap. Atualizar só com smoke visual e medição antes e depois.
- **Paths:** `prototype/cerebro-semantico-3d.html` (importmap no `<head>`)

### ADR-007: GLSL sem NaN

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** Numa GPU real, `pow` com base negativa gerou NaN, e o bloom espalhou o NaN em blocos pretos no centro da tela. No SwiftShader o defeito não aparecia.
- **Decisão:** Toda base de `pow` passa por `max(..., 0.0)` ou `clamp`. Todo `normalize` de vetor que pode zerar recebe `+ 1e-6`.
- **Consequência:** Shader novo segue a mesma regra. Teste em SwiftShader não prova ausência de NaN.
- **Paths:** seção 3 do viewer

### ADR-008: Defeito visual só por medição

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** Impressão sobre screenshot reduzido levou a ajustes errados de brilho.
- **Decisão:** Brilho e estouro se julgam com `tools/visual/measure.py` em 1440x900. Referência: 3,3% de pixels saturados na visão geral do grafo real foi aceito; 23% foi estouro.
- **Paths:** `tools/visual/`

### ADR-009: Calor por atividade com meia-vida de 3 semanas

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O peso por grau mostrava o que é central, não o que está vivo.
- **Decisão:** Atividade = fatos datados da nota + eventos que apontam para ela, por semana. Calor acumula com decaimento `0.5^(1/3)` por semana e é normalizado pelo máximo global com raiz quadrada. Data posterior a `until` não conta.
- **Paths:** `pipeline/build_graph.py` (bloco "atividade semanal"), seção 7 do viewer (`heatAt`)

### ADR-010: Equivalência com o pipeline de origem

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O código veio de scripts que rodam semanalmente sobre um vault real.
- **Decisão:** A generalização foi aceita porque, com um config que reproduz as regras originais, as cinco etapas (grafo, embed, lint, linha do tempo, extratos e aliases) deram saída idêntica byte a byte sobre os dados reais. O config de equivalência fica fora do repo.
- **Consequência:** Mudança de regra que altera a saída precisa de ADR e de regeneração dos artefatos de exemplo.

### ADR-011: Publicação em duas fases

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O projeto nasceu sobre dados pessoais. Um vazamento no histórico do git não se desfaz com commit novo.
- **Decisão:** Repositório na conta pessoal do mantenedor, privado primeiro. Vira público só com ok explícito do mantenedor, depois do checklist da fase 2 em `docs/HANDOFF.md`, com evidência de cada item.
- **Consequência:** Nenhum agente muda a visibilidade por conta própria. Achado sensível no histórico bloqueia a abertura até o histórico ser reescrito.
- **Paths:** `docs/HANDOFF.md` (seção Publicação)

### ADR-012: Licença MIT

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** A fase 2 da publicação exige licença decidida. As opções eram MIT e AGPL.
- **Decisão:** MIT, por escolha do mantenedor.
- **Consequência:** Qualquer um pode reutilizar o código, inclusive em produto fechado, desde que mantenha o aviso de copyright. Trocar de licença depois de público exige novo ADR.
- **Paths:** `LICENSE`, `README.md` (seção Licença)

### ADR-013: JID fora dos extratos de mensagens

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** `prep_messages.py` só redigia o texto. Remetente sem nome saía como o número do JID, conversa sem nome saía como o próprio JID no cabeçalho, e o nome do remetente era cortado em 18 caracteres antes de qualquer redação.
- **Decisão:** Remetente sem nome vira `?` e conversa sem nome vira `[sem nome]`. Nome igual a um JID conta como sem nome. Nome de remetente e de conversa passam por `redact()` antes do corte. Quando o nome falta ou a redação o alterou, o JID separa as conversas só na chave interna, para duas conversas `[TEL]` não se fundirem. Nas conversas não sigilosas os nomes continuam, por decisão do mantenedor.
- **Consequência:** Com nomes que a redação não altera, a saída não muda. Testes em `tests/test_prep_messages.py` falham se um JID ou telefone voltar a aparecer. Número estrangeiro ou sem DDD usado como nome passa inteiro, como já passa no texto (limite de `redact()` declarado em `docs/PRIVACIDADE.md`).
- **Paths:** `pipeline/prep_messages.py`, `tests/test_prep_messages.py`

### ADR-014: Evidência de publicação e origem do preview

- **Data:** 2026-10-21
- **Status:** accepted
- **Contexto:** O detector de histórico acusava os noreply aceitos; a captura anterior não tinha registro reproduzível da origem.
- **Decisão:** Preservar achados brutos e liberar no conteúdo somente os dois endereços noreply completos conhecidos. O e-mail pessoal aceito como autor não é liberado no conteúdo. Capturar o exemplo pelo smoke, em PNG, com hashes das fontes e da imagem, revisão de origem e identificador do run quando gerado no CI.
- **Consequência:** Outros endereços continuam bloqueando. Mudança na imagem ou nas fontes invalida a verificação de origem até regenerar. O procedimento é reproduzível, mas os pixels da animação podem variar. A publicação continua dependendo do ok do mantenedor após o checklist.
- **Paths:** `scripts/check_publication.py`, `tools/visual/preview.py`, `docs/img/preview-origin.json`, `docs/HANDOFF.md`
