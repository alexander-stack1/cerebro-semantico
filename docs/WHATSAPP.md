# WhatsApp: formar um histórico no vault

**Português** | [English](en/WHATSAPP.md) · [README](../README.md)

Esta versão foi preparada especialmente para formar histórico a partir de mensagens coletadas pela API do WhatsApp por uma integração externa. A coleta, autenticação, paginação ou backfill, armazenamento incremental e deduplicação pertencem a um adaptador externo. Esse adaptador deve entregar ao pipeline somente as mensagens novas desde a execução anterior. O pipeline não mantém cursor, não consulta a API e não deduplica mensagens.

O histórico é formado aos poucos: um modelo atualiza as notas Markdown com base em cada lote novo de extratos redigidos. A linha do tempo e o grafo são reconstruídos a partir do vault acumulado.

```text
API/integração externa → NDJSON novo → extratos redigidos → modelo externo → notas Markdown
    → lint → linha do tempo → grafo JSON → HTML interativo
```

## 1. Prepare a configuração e o mapa privado

Use Python 3.9 ou superior. O processamento local usa somente a biblioteca padrão.

```bash
cp config/config.example.json config/config.json
mkdir -p private extratos out
```

Edite `config/config.json` para apontar `vault.path` para seu vault e ajustar categorias, pastas e segmentos. O exemplo configura estes caminhos relativos ao arquivo de configuração:

- `private.chat_map`: `../private/chat_map.json`, classificação de conversas;
- `private.aliases`: `../private/aliases.json`, aliases estáveis das conversas sigilosas. O script cria ou atualiza este arquivo;
- `private.sensitive_names`: `../private/sensitive_names.txt`, nomes extras que o lint deve procurar.

O mapa de conversas tem o formato abaixo. `by_jid` classifica pelo identificador do chat e `by_name` oferece uma alternativa pelo nome. Preencha esses valores localmente com seus dados; não os copie para o repositório.

```json
{
  "by_jid": {
    "chat-demo-01": {"dom": "Profissional", "sub": "Equipe"}
  },
  "by_name": {
    "Conversa de exemplo": {"dom": "Profissional", "sub": "Equipe"}
  }
}
```

Para uma conversa sigilosa, configure uma subcategoria que comece com um dos valores de `messages.sensitive_sub_prefixes`. O pipeline substitui o nome por um alias estável, como `Novo-01`, e mantém a associação com o nome somente em `private/aliases.json`. A regra `messages.sensitive_name_regex` também pode identificar conversas individuais desconhecidas. Revise essas regras antes de processar dados.

## 2. Exporte apenas mensagens novas para NDJSON

O adaptador externo deve transformar cada mensagem em um objeto JSON por linha UTF-8. Campos reconhecidos:

| Campo | Uso no pipeline |
|---|---|
| `chat_jid` | Obrigatório. Identifica a conversa para consultar o mapa e manter aliases. Não é escrito no extrato. |
| `from_me` | Obrigatório, booleano. Seleciona o rótulo de remetente configurado para mensagens próprias. |
| `timestamp` | Obrigatório. Data ISO 8601 em UTC; o script aplica `messages.timezone_offset_hours`. |
| `chat_name` | Opcional. Nome da conversa, usado na classificação por nome e no cabeçalho após redação. |
| `sender_name` | Opcional. Nome exibido do remetente, após redação, limitado a 18 caracteres. Se ausente ou parecido com JID, vira `?`. |
| `text` | Opcional. Texto da mensagem. O script redige padrões conhecidos e limita caracteres. |
| `transcript` | Opcional. Transcrição de áudio; usada quando `text` é um marcador de mídia ou está vazio. |
| `sender_jid` | Pode vir na exportação, mas o pipeline não o utiliza. |

Para grupos, o `chat_jid` deve terminar em `@g.us`: o pipeline usa esse sufixo para reconhecer grupos e aplicar a amostragem. Se o adaptador substituir o identificador por um valor opaco, preserve o sufixo e use o mesmo valor no `chat_map.json`. Sem ele, o grupo será tratado como conversa individual e a amostragem de grupos não será aplicada. O exemplo abaixo representa uma conversa individual.

Exemplo sintético com identificadores ilustrativos. O adaptador deve mapear os identificadores reais de forma consistente, somente no ambiente privado:

```json
{"chat_jid":"chat-demo-01","chat_name":"Conversa de exemplo","from_me":false,"sender_name":"Contato de exemplo","sender_jid":"remetente-demo-01","text":"Mensagem totalmente fictícia.","timestamp":"2026-10-20T14:30:00Z"}
```

Uma mensagem por linha. Antes de cada execução, o adaptador deve selecionar só registros posteriores ao último lote concluído, usando identificadores ou cursores da API do lado externo. Não reenvie a exportação histórica completa: este comando não elimina duplicatas e elas reapareceriam nos extratos. Uma carga inicial histórica também exige backfill feito pelo adaptador externo; depois dela, envie somente novidades.

## 3. Gere extratos redigidos

Grave o lote NDJSON localmente, em local ignorado pelo Git, e rode:

```bash
python3 pipeline/prep_messages.py \
  --config config/config.json \
  --new private/novas-mensagens.ndjson \
  --out extratos/
```

Os extratos são temporários: cada execução substitui os arquivos dos segmentos configurados na pasta de saída. O histórico durável fica no vault, não nessa pasta. Preserve o lote de entrada no armazenamento privado da integração e avance o cursor somente depois de aplicar e validar as notas. Use identificadores de mensagens para controlar duplicatas e mensagens recebidas com atraso, em vez de depender apenas da data.

O script consulta `chat_map.json`, segmenta as conversas pelas regras de `messages.segments` e grava arquivos `.txt` em `extratos/`. Também atualiza `aliases.json`. Conversas sem classificação usam o segmento padrão. Grupos acima do limite configurado são amostrados; mensagens próprias são mantidas e as demais são amostradas conforme a configuração.

O texto, nomes de conversa e nomes de remetente passam por padrões de redação conhecidos antes de irem para os extratos. Isso não garante anonimização. A redação não cobre todos os nomes, endereços, dados escritos por extenso ou arquivos de mídia sem transcrição. Não envie conteúdo que não seja necessário ao modelo. Consulte [Privacidade](PRIVACIDADE.md).

## 4. Atualize o vault e confira

Use [o briefing incluído](../pipeline/briefing.template.md) como base das instruções. Envie ao modelo externo somente os extratos necessários, junto das notas relevantes do vault e de instruções de atualização. O modelo não é executado nem chamado por este repositório. Revise a resposta e aplique as alterações às notas Markdown. Não substitua o vault inteiro pelo extrato e não trate uma redação como autorização para compartilhar dados.

Depois de atualizar as notas, execute o lint:

```bash
python3 pipeline/lint_vault.py --config config/config.json
```

O lint falha para os tipos de dado sigiloso e nomes configurados que detecta. Frases de estilo e links quebrados geram avisos. A ausência de achados não prova que o vault esteja anonimizado.

## 5. Reconstrua linha do tempo e visualização

Use uma data de corte ISO `AAAA-MM-DD` para separar eventos futuros:

```bash
python3 pipeline/timeline.py \
  --config config/config.json \
  --csv out/eventos.csv \
  --until 2026-10-21
python3 pipeline/build_graph.py \
  --config config/config.json \
  --out out/grafo.json \
  --source "Vault atualizado" \
  --until 2026-10-21
python3 pipeline/embed_viewer.py \
  --template prototype/cerebro-semantico-3d.html \
  --json out/grafo.json \
  --out out/cerebro.html
```

`timeline.py` grava o CSV e notas mensais, índice e eventos futuros na pasta definida em `timeline.folder` dentro do vault. `build_graph.py` lê o vault configurado e pode falhar se encontrar nomes segundo sua varredura. `embed_viewer.py` gera um HTML com o grafo embutido. A página carrega Three.js e GSAP do jsDelivr, portanto o navegador precisa de conexão.

## O que não está incluído

Não há cliente da API WhatsApp, webhook, agendador, coleta automática, autenticação, armazenamento incremental, cursor, backfill ou deduplicação. Também não há chamada automática a um modelo nem escrita automática das notas. A integração externa deve cuidar da coleta e da seleção incremental; uma pessoa deve revisar a atualização do vault e a página antes de compartilhá-la.
