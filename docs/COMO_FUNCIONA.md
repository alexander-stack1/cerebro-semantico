# Como funciona

O Cérebro Semântico transforma notas Markdown em dados de um grafo e incorpora esses dados em um visualizador HTML interativo. O processamento é local: você aponta a configuração para o vault e executa os scripts. O exemplo incluído é fictício.

## Caminho principal

```text
Vault Markdown → build_graph.py → grafo JSON → embed_viewer.py → página HTML
```

1. `pipeline/config.py` combina `config/config.example.json` com os padrões e valida categorias, lobos e regras de pasta.
2. `pipeline/vault.py` percorre arquivos `.md`, lê frontmatter em linhas simples, `[[wikilinks]]`, datas e eventos.
3. `pipeline/build_graph.py` escolhe as notas incluídas, calcula conexões e atividade, e grava o JSON. O script encerra com erro se a varredura configurada encontrar nome de pessoa no resultado.
4. `pipeline/embed_viewer.py` insere o JSON na constante `BRAIN_DATA` do protótipo, produzindo uma página HTML independente do arquivo de dados.
5. O navegador desenha o cérebro procedural, os neurônios, as conexões, os rótulos e os controles. Three.js r160 e GSAP 3.12.5 são carregados do jsDelivr.

## Como os dados viram grafo

Cada nota mantida vira um nó, classificado por título ou pelas regras de pasta. Notas configuradas como pessoas, hubs, eventos, períodos e outros tipos excluídos não viram nós, embora links para notas excluídas possam contribuir para relações latentes.

- **Conexão direta:** duas notas têm uma conexão quando existe wikilink entre elas. A proximidade considera valor-base, reciprocidade, vizinhos em comum e pasta compartilhada.
- **Conexão latente:** relação calculada entre notas sem conexão direta que compartilham uma nota excluída elegível ou pelo menos duas tags. Há limite por nó e o valor é menor que o das conexões diretas. “Latente” descreve essa regra do grafo; não significa que uma IA inferiu uma relação.
- **Peso:** deriva do número de conexões diretas em relação ao nó de maior grau.
- **Atividade:** linhas com data e eventos que apontam para a nota são agrupados em semanas. Datas posteriores ao fim selecionado não contam como atividade.
- **Calor:** a visualização acumula atividade semanal, reduzindo a contribuição anterior por um fator de decaimento. A meia-vida é de três semanas: após três semanas, uma contribuição anterior vale metade. O resultado é normalizado para dimensionar e iluminar os nós.

O protótipo posiciona os nós nos lobos definidos pelas categorias. A interação inclui busca, seleção e foco por categoria. A linha do tempo permite percorrer as semanas e observar como os registros se distribuem.

## Formato das notas

Um arquivo Markdown corresponde a uma nota. O título é o nome do arquivo sem `.md`. O frontmatter é opcional e reconhece pares simples como `tipo: tema`, `dominio: Trabalho`, `tags: alpha, beta` e `confianca: alta`. O parser não é YAML completo: não interpreta listas, estruturas aninhadas ou frontmatter multilinha.

Use `[[Título da nota]]` para uma ligação. Datas de atividade podem ser registradas em linhas iniciadas por `- AAAA-MM-DD`. Notas de evento cujo nome começa pelo prefixo configurado aceitam linhas no formato:

```text
- 2026-05-14 | Trabalho | Revisão do projeto | [[Projeto]]
```

O detalhe do esquema está em [Formato do grafo](FORMATO_GRAFO.md); o vault fictício de exemplo fica em [../examples/vault/](../examples/vault/).

## Fluxo opcional de mensagens e linha do tempo

`pipeline/prep_messages.py` recebe mensagens em NDJSON e gera extratos segmentados. Usa o mapa local de conversas, pode trocar conversas sigilosas por aliases, redige padrões conhecidos e limita o tamanho das mensagens. Um modelo pode usar os extratos com as instruções de `pipeline/briefing.template.md` para atualizar notas.

Depois, `pipeline/lint_vault.py` verifica dados que reconhece, nomes sigilosos configurados, frases e links quebrados. Achados de sigilo encerram o comando com erro; estilo e links quebrados são avisos. `pipeline/timeline.py` converte linhas de evento em CSV, notas mensais, índice e uma nota separada para eventos futuros. Essa ferramenta grava no vault de destino.

Essas etapas são opcionais. O usuário escolhe e configura ferramentas e modelo externos. Leia [Privacidade](PRIVACIDADE.md) antes de processar dados reais.

## Limites e pressupostos

- A redação cobre padrões conhecidos, sobretudo formatos brasileiros. Não detecta de forma abrangente nomes no texto, endereços, datas de nascimento, dados escritos por extenso, conteúdo em imagem ou áudio sem transcrição, nem formatos de outros países. Não é garantia de anonimização.
- A varredura de nomes depende das notas do tipo configurado, das listas e exceções locais. Uma checagem sem ocorrências não prova ausência de dado pessoal.
- O grafo expõe títulos e relações das notas embutidas. Revise o HTML antes de compartilhar.
- A página pode ser aberta como arquivo local, mas depende de rede para baixar Three.js e GSAP pelo jsDelivr. A reprodução de vídeo da galeria é manual, acionada pelo link da miniatura.
- As imagens e os vídeos da galeria são capturas reais em Chromium com renderização por software SwiftShader, sem áudio. A fluidez pode ser limitada pela ausência de GPU e não mede o desempenho em GPU. [docs/media/origin.json](media/origin.json) registra a origem e os hashes. Confira com `python3 tools/visual/demo_media.py --verify-ci`.
- O pipeline usa Python 3.9+ e biblioteca padrão. Os testes também usam `unittest` da biblioteca padrão. O smoke visual é opcional e requer Playwright, Pillow e NumPy.
- Safari e Firefox: **NÃO VERIFICADO**. O comportamento de Windows e frontmatter YAML multilinha também está marcado como não verificado no mapa do repositório.

## Verificação local

```bash
python3 -m unittest discover -s tests
python3 scripts/check_size.py
```

Para testar a renderização em Chromium, instale as dependências opcionais e execute `python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html`.
