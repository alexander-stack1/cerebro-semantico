# WhatsApp: building a vault history

[Português](../WHATSAPP.md) | **English** · [README](../../README.en.md)

This version is designed especially to build a history from messages collected through the WhatsApp API by an external integration. Collection, authentication, pagination or backfill, incremental storage, and deduplication belong to an external adapter. That adapter must send the pipeline only messages that are new since the previous run. The pipeline does not keep a cursor, query the API, or deduplicate messages.

The history grows over time: an external model updates Markdown notes from each new batch of redacted extracts. The timeline and graph are rebuilt from the accumulated vault.

```text
External API/integration → new NDJSON → redacted extracts → external model → Markdown notes
    → lint → timeline → graph JSON → interactive HTML
```

## 1. Prepare the configuration and private map

Use Python 3.9 or newer. Local processing uses only the Python standard library.

```bash
cp config/config.example.json config/config.json
mkdir -p private extratos out
```

Edit `config/config.json` to point `vault.path` to your vault and adjust categories, folders, and message segments. The example config resolves these paths relative to the config file:

- `private.chat_map`: `../private/chat_map.json`, for conversation classification;
- `private.aliases`: `../private/aliases.json`, for stable aliases of sensitive conversations. The script creates or updates this file;
- `private.sensitive_names`: `../private/sensitive_names.txt`, for extra names the lint should check.

The conversation map has the structure below. `by_jid` classifies by chat identifier; `by_name` is a fallback. Populate these values locally with your data. Do not copy them into the repository.

```json
{
  "by_jid": {
    "chat-demo-01": {"dom": "Profissional", "sub": "Equipe"}
  },
  "by_name": {
    "Example conversation": {"dom": "Profissional", "sub": "Equipe"}
  }
}
```

The classification values `Profissional` and `Equipe` match the Portuguese example configuration. Keep them aligned with your configured segment rules.

For a sensitive conversation, configure a subcategory beginning with one of the values in `messages.sensitive_sub_prefixes`. The pipeline replaces its name with a stable alias such as `Novo-01` and stores the name-to-alias mapping only in `private/aliases.json`. `messages.sensitive_name_regex` can also identify unknown one-to-one conversations. Review these rules before processing messages.

## 2. Export only new messages as NDJSON

The external adapter must convert each message into one UTF-8 JSON object per line. Recognized fields:

| Field | Pipeline use |
|---|---|
| `chat_jid` | Required. Identifies the conversation for map lookup and stable aliases. It is not written to extracts. |
| `from_me` | Required boolean. Selects the configured label for messages sent by you. |
| `timestamp` | Required. ISO 8601 date and time in UTC; the script applies `messages.timezone_offset_hours`. |
| `chat_name` | Optional. Conversation name, used for name-based classification and, after redaction, in the extract header. |
| `sender_name` | Optional. Display name for the sender, after redaction and limited to 18 characters. Missing values or JID-like values become `?`. |
| `text` | Optional. Message text. Known patterns are redacted and the text is limited to the configured character count. |
| `transcript` | Optional. Audio transcript, used when `text` is a media placeholder or empty. |
| `sender_jid` | May be present in an export, but the pipeline does not use it. |

Synthetic example with illustrative identifiers. Your adapter must map real identifiers consistently, only in your private environment:

```json
{"chat_jid":"chat-demo-01","chat_name":"Example conversation","from_me":false,"sender_name":"Example contact","sender_jid":"sender-demo-01","text":"Entirely fictional message.","timestamp":"2026-10-20T14:30:00Z"}
```

Use one message per line. Before each run, the adapter must select records newer than the last completed batch, using API identifiers or cursors outside this repository. Do not resend the full historical export: this command does not deduplicate messages, so duplicates would reappear in the extracts. An initial historical import also requires a backfill by the external adapter; send only new messages after that import.

## 3. Generate redacted extracts

Save the NDJSON batch locally in a Git-ignored location and run:

```bash
python3 pipeline/prep_messages.py \
  --config config/config.json \
  --new private/new-messages.ndjson \
  --out extratos/
```

Extracts are temporary: each run replaces the configured segment files in the output folder. Durable history lives in the vault, not in that folder. Retain the input batch in your integration’s private storage and advance the cursor only after applying and validating the notes. Track message identifiers to handle duplicates and late arrivals rather than relying only on timestamps.

The script reads `chat_map.json`, segments conversations according to `messages.segments`, and writes `.txt` files to `extratos/`. It also updates `aliases.json`. Unclassified conversations use the default segment. Groups above the configured threshold are sampled: messages sent by you are retained, while other messages are sampled according to the configuration.

## Privacy

Message text, conversation names, and sender names pass through known redaction patterns before they reach the extracts. This is not guaranteed anonymization. Redaction does not cover every name, address, spelled-out identifier, or media file without a transcript. Send the model only what it needs. See [Privacy](../PRIVACIDADE.md).

## 4. Update and check the vault

Use [the included briefing template](../../pipeline/briefing.template.md) as a starting point for instructions. Send only the necessary extracts and relevant vault notes to the external model, with instructions for updating the notes. This repository does not run or call a model. Review its response and apply changes to the Markdown notes. Do not replace the whole vault with an extract or treat redaction as permission to share data.

After updating the notes, run the linter:

```bash
python3 pipeline/lint_vault.py --config config/config.json
```

The linter fails on the sensitive data types and configured names it detects. Style phrases and broken links produce warnings. No findings do not prove that a vault is anonymized.

## 5. Rebuild the timeline and visualization

Use an ISO `YYYY-MM-DD` cutoff to separate future events:

```bash
python3 pipeline/timeline.py \
  --config config/config.json \
  --csv out/events.csv \
  --until 2026-10-21
python3 pipeline/build_graph.py \
  --config config/config.json \
  --out out/graph.json \
  --source "Updated vault" \
  --until 2026-10-21
python3 pipeline/embed_viewer.py \
  --template prototype/cerebro-semantico-3d.html \
  --json out/graph.json \
  --out out/brain.html
```

`timeline.py` writes the CSV and monthly notes, index, and future-events note to `timeline.folder` inside the vault. `build_graph.py` reads the configured vault and may fail if its configured name scan finds a match. `embed_viewer.py` creates an HTML file with the graph embedded. The page loads Three.js and GSAP from jsDelivr, so the browser needs an internet connection.

## What is not included

There is no WhatsApp API client, webhook, scheduler, automatic collection, authentication, incremental storage, cursor, backfill, or deduplication. There is also no automatic model call or automatic note writing. The external integration must collect and select incremental messages; a person should review vault updates and the page before sharing them.
