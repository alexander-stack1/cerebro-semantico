# Cérebro Semântico

[![CI](https://github.com/alexander-stack1/cerebro-semantico/actions/workflows/ci.yml/badge.svg)](https://github.com/alexander-stack1/cerebro-semantico/actions/workflows/ci.yml)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

> Converte notas Markdown no formato Obsidian em um grafo de temas e explora as conexões em um cérebro 3D interativo.

![Visão geral do cérebro 3D](docs/media/visao-geral.png)

## Sumário

- [Início rápido](#início-rápido)
- [Galeria](#galeria)
- [Capacidades e limites](#capacidades-e-limites)
- [Documentação](#documentação)

## Início rápido

Para abrir a demonstração localmente, clone o repositório e abra o arquivo HTML no navegador. O link do HTML no GitHub exibe o código-fonte, não executa a aplicação. O grafo embutido é fictício. O navegador precisa de internet para carregar Three.js e GSAP pelo jsDelivr.

```bash
git clone https://github.com/alexander-stack1/cerebro-semantico.git
cd cerebro-semantico
open prototype/cerebro-semantico-3d.html  # macOS; em outros sistemas, abra o arquivo no navegador
```

Controles: arraste para orbitar, use o scroll para aproximar ou afastar e clique num neurônio para selecioná-lo. `Esc` limpa a seleção e retorna à visão geral. Pressione `/` para buscar e use a linha do tempo na parte inferior direita para percorrer as semanas.

Para gerar uma visualização com seu vault, use Python 3.9 ou superior. O pipeline não exige pacotes Python externos:

```bash
cp config/config.example.json config/config.json  # arquivo local ignorado pelo Git
# Edite categories, vault.path, vault.folders e timeline.start.
python3 pipeline/build_graph.py --config config/config.json --out out/grafo.json --source "Minhas notas"
python3 pipeline/embed_viewer.py --template prototype/cerebro-semantico-3d.html \
    --json out/grafo.json --out out/meu-cerebro.html
```

O vault usa notas `.md`, frontmatter simples em linhas `chave: valor`, wikilinks `[[Título]]` e linhas datadas `- AAAA-MM-DD`. Categorias e pastas são definidas na configuração. Veja o [formato esperado](docs/FORMATO_GRAFO.md) e o [funcionamento detalhado](docs/COMO_FUNCIONA.md).

## Galeria

As imagens mostram a visão geral, o tema selecionado e a linha do tempo. Clique nas miniaturas para abrir os vídeos correspondentes.

| Visão geral | Tema ativo | Linha do tempo |
|---|---|---|
| ![Visão geral do cérebro 3D](docs/media/visao-geral.png) | ![Tema selecionado no cérebro](docs/media/tema-ativo.png) | ![Linha do tempo do cérebro](docs/media/linha-do-tempo.png) |

| Demonstração | Demonstração da linha do tempo |
|---|---|
| [![Assistir à navegação no cérebro](docs/media/visao-geral.png)](docs/media/navegacao.mp4) | [![Assistir à linha do tempo](docs/media/linha-do-tempo.png)](docs/media/linha-do-tempo.mp4) |

As miniaturas são links para os arquivos de vídeo. A reprodução depende do visualizador de Markdown ou navegador.

As mídias são capturas reais do Chromium com renderização por software SwiftShader, sem áudio. A fluidez pode ser limitada pelo renderizador sem GPU e não representa o desempenho em GPU. A origem e os hashes estão em [docs/media/origin.json](docs/media/origin.json). Verifique a captura e o artefato de CI com `python3 tools/visual/demo_media.py --verify-ci`.

## Capacidades e limites

- O pipeline constrói conexões diretas a partir de wikilinks e conexões latentes a partir de temas compartilhados. O peso do nó considera seu grau no grafo.
- O calor da atividade semanal usa meia-vida de três semanas: após esse intervalo, a contribuição de uma semana anterior cai pela metade. Conexões latentes representam relações calculadas por notas ou tags compartilhadas; não são inferências de inteligência artificial.
- Registros datados alimentam atividade semanal; o visualizador oferece busca, seleção, foco por categoria e linha do tempo.
- Ferramentas opcionais preparam extratos de mensagens com redação de padrões conhecidos, validam notas e montam linha do tempo mensal e CSV. O uso com dados reais exige ler [Privacidade](docs/PRIVACIDADE.md).
- Redação não é anonimização garantida: nomes no texto, dados escritos por extenso, conteúdo de arquivos e formatos de outros países podem passar. Revise antes de compartilhar.
- O parser não implementa YAML completo. Não aceita frontmatter multilinha. O visualizador depende do CDN e a compatibilidade documentada foi verificada em Chrome; Safari e Firefox são **NÃO VERIFICADO**.

## Documentação

- [Como funciona](docs/COMO_FUNCIONA.md)
- [Roteiros e reprodução das demonstrações](docs/DEMONSTRACOES.md)
- [Formato do grafo](docs/FORMATO_GRAFO.md)
- [Privacidade e limites da redação](docs/PRIVACIDADE.md)
- [Mapa do repositório](docs/agent/REPO_MAP.md)

Captura do exemplo: [imagem](docs/img/preview.png) · [proveniência e hashes](docs/img/preview-origin.json). Verifique a origem com `python3 tools/visual/preview.py --check --verify-ci`.

## English summary

Cérebro Semântico turns an Obsidian-style Markdown vault into an interactive 3D brain. Topic notes become neurons placed in the lobe of their area, wikilinks become synapses, and a weekly timeline shows how “hot” each topic was. Open `prototype/cerebro-semantico-3d.html` to see the fictional example. To use your own vault, copy `config/config.example.json`, then run `pipeline/build_graph.py` and `pipeline/embed_viewer.py`. The pipeline is pure Python standard library (3.9+). An optional message pipeline redacts personal data (Brazilian formats) before any text reaches a language model. The UI and docs are in Brazilian Portuguese.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests
python3 scripts/check_size.py
```

O pipeline e os testes usam apenas a biblioteca padrão. O smoke visual é opcional e requer Playwright, Pillow e NumPy: `python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html`.

## Licença

[MIT](LICENSE).
