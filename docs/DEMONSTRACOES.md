# Capturas e vídeos

As mídias em `docs/media/` mostram o vault fictício de `examples/` no próprio visualizador. Não há dados de usuário nem imagens geradas por IA.

## Roteiros

| Arquivo | Conteúdo |
|---|---|
| `visao-geral.png` | Cérebro com o grafo de exemplo |
| `tema-ativo.png` | Busca e seleção de “Reforma do banheiro”, com painel de conexões |
| `linha-do-tempo.png` | Semana intermediária após reproduzir a linha do tempo |
| `navegacao.mp4` | Visão geral, busca, seleção do tema e retorno por Esc |
| `linha-do-tempo.mp4` | Primeira semana, reprodução, pausa e última semana |

Os MP4 usam H.264, formato de pixel yuv420p e faststart. São gravações da aplicação, sem áudio. O início do carregamento é cortado, sem acelerar o restante. A captura usa Chromium com renderização por software SwiftShader; a fluidez depende do runner e não mede o desempenho com GPU.

## Reproduzir

```bash
python3 -m pip install playwright==1.64.0
python3 -m playwright install --with-deps chromium
# Instale ffmpeg e ffprobe pelo gerenciador de pacotes do sistema.
python3 tools/visual/demo_media.py
```

O fluxo de publicação usa o workflow [demonstrações](../.github/workflows/media.yml), que executa o roteiro e disponibiliza os arquivos no artefato `demo-<revisão>`. A verificação de publicação exige o identificador do run; uma execução local pode produzir a mídia, mas encerra com erro nessa verificação se não houver run de origem.

Antes de gravar, o script confirma que o HTML embute exatamente `examples/sample_graph.json` e roda os testes de reprodução do exemplo. Durante a captura verifica a seleção do tema, a mudança de semana e a ausência de erros JavaScript. `ffprobe` verifica codec, dimensões e duração; `ffmpeg` decodifica integralmente os vídeos e falha em erro. As verificações locais também exigem essas duas ferramentas.

## Conferir a origem

[origin.json](media/origin.json) registra revisões de origem, run, observações da interface, metadados dos vídeos e SHA-256 das fontes e mídias.

```bash
python3 tools/visual/demo_media.py --check
python3 tools/visual/demo_media.py --verify-ci  # requer gh autenticado enquanto o repo for privado
```

O segundo comando exige run bem-sucedido no workflow esperado e compara os arquivos locais, inclusive o manifesto, byte a byte com o artefato baixado. A retenção do artefato no GitHub é finita; se expirar, gere nova captura para renovar a prova remota. A animação pode produzir pixels diferentes a cada execução.

Para atualizar, execute o workflow, inspecione imagens e vídeos, copie o artefato completo para `docs/media/`, rode os dois comandos e versione os arquivos juntos. Nunca substitua somente a imagem ou somente o manifesto.


## Prévia animada e acesso ao MP4

O MP4 está versionado, mas a página de arquivo do GitHub pode mostrar apenas “View raw”. Os READMEs em português e inglês usam links diretos de download, evitando essa página intermediária. Abra o MP4 baixado no player local. O acesso ao repositório privado continua exigindo autenticação.

Os GIFs mostram trechos reais de 30 segundos, a 4 quadros por segundo, sem acelerar a gravação. Navegação usa o intervalo de 20 a 50 segundos; linha do tempo, de 15 a 45 segundos. A resolução da prévia é 720x450. Os MP4s completos continuam em 1440x900.

```bash
python3 tools/visual/animated_preview.py          # requer ffmpeg/ffprobe
python3 tools/visual/animated_preview.py --check  # biblioteca padrão
```

[animated-origin.json](media/animated-origin.json) registra os comandos, a versão de ffmpeg e os hashes dos MP4s, do manifesto original, do gerador e dos GIFs. A geração verifica os vídeos de origem e confirma 120 quadros por GIF. Os testes protegem os hashes das prévias versionadas; a verificação remota dos MP4s continua em `demo_media.py --verify-ci`.
