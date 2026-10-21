# How it works

[Português](../COMO_FUNCIONA.md) | **English** · [README](../../README.en.md)

Cérebro Semântico turns Markdown notes into graph data and embeds that data in an interactive HTML viewer. The pipeline runs locally: point the configuration at a vault and run the scripts. The included sample is fictional.

This version is designed especially to build history from messages collected through the WhatsApp API by an external integration. The pipeline accepts normalized NDJSON; collection, webhooks and historical imports belong to that integration. See the [WhatsApp history workflow](WHATSAPP.md).

## Main flow

```text
Markdown vault → build_graph.py → graph JSON → embed_viewer.py → HTML page
```

1. `pipeline/config.py` merges `config/config.example.json` with defaults and validates categories, lobes, and folder rules.
2. `pipeline/vault.py` walks `.md` files and reads simple frontmatter lines, `[[wikilinks]]`, dates, and events.
3. `pipeline/build_graph.py` selects included notes, calculates connections and activity, and writes JSON. It exits with an error if its configured scan finds a person's name in the output.
4. `pipeline/embed_viewer.py` inserts the JSON into the prototype's `BRAIN_DATA` constant, producing an HTML page that contains its graph data.
5. The browser draws the procedural brain, neurons, connections, labels, and controls. Three.js r160 and GSAP 3.12.5 load from jsDelivr.

## How notes become a graph

Each included note becomes a node, categorized by title or folder rules. Notes configured as people, hubs, events, periods, and other excluded types do not become nodes. Links to excluded notes can still contribute to latent connections.

- **Direct connection:** two notes have a connection when a wikilink joins them. Proximity considers a base value, reciprocal links, shared neighbors, and a shared folder.
- **Latent connection:** a calculated relationship between notes without a direct link when they share an eligible excluded note or at least two tags. There is a per-node cap, and the connection value is lower than for direct links. “Latent” describes this graph rule; it does not mean an AI inferred the relationship.
- **Weight:** derives from the number of direct connections relative to the highest-degree node.
- **Activity:** dated lines and events that link to a note are grouped by week. Dates after the selected cutoff do not count as activity.
- **Heat:** the viewer accumulates weekly activity while decaying earlier contributions. Its half-life is three weeks: after three weeks, an earlier contribution is worth half as much. The result is normalized to size and light the nodes.

The prototype places nodes in lobes assigned to their categories. Interaction includes search, selection, and category focus. The timeline lets you move through weeks and observe how records are distributed.

## Note format

One Markdown file represents one note. Its title is the file name without `.md`. Optional frontmatter uses simple key-value lines such as `tipo: tema`, `dominio: Trabalho`, `tags: alpha, beta`, and `confianca: alta`. The parser is not a full YAML parser: it does not interpret lists, nested structures, or multiline frontmatter.

Use `[[Note title]]` for a link. Record activity with lines beginning `- YYYY-MM-DD`. Event notes whose names start with the configured prefix accept lines in this format:

```text
- 2026-05-14 | Work | Project review | [[Project]]
```

See the [graph format](../FORMATO_GRAFO.md) and the fictional [sample vault](../../examples/vault/).

## Optional message and timeline flow

`pipeline/prep_messages.py` accepts NDJSON messages and generates segmented extracts. It uses a local conversation map, can replace sensitive conversations with aliases, redacts known patterns, and limits message length. An external model can use the extracts with `pipeline/briefing.template.md` to update notes.

Then `pipeline/lint_vault.py` checks for recognized sensitive data, configured sensitive names, style issues, and broken links. Sensitive-data findings make the command fail; style and broken links are warnings. `pipeline/timeline.py` turns event lines into a CSV, monthly notes, an index, and a separate note for future events. This tool writes to the target vault.

These steps are optional. The user chooses and configures any external tools and model. Read [Privacy](../PRIVACIDADE.md) before processing real data. For the WhatsApp-oriented workflow, see [WhatsApp guide](WHATSAPP.md).

## Limits and assumptions

- Redaction covers known patterns, mainly Brazilian formats. It does not comprehensively detect names in text, addresses, birth dates, spelled-out personal data, content in images or audio without a transcript, or formats from other countries. It is not guaranteed anonymization.
- Name scanning depends on notes of the configured type, local lists, and exceptions. A clean scan does not prove there is no personal data.
- The graph exposes embedded note titles and relationships. Review the HTML before sharing it.
- The page can be opened as a local file, but it needs a network connection to download Three.js and GSAP from jsDelivr. Gallery videos open only when the thumbnail link is clicked.
- The pipeline uses Python 3.9+ and the standard library. Tests also use the standard-library `unittest`. The visual smoke test is optional and requires Playwright, Pillow, and NumPy.
- Safari and Firefox: **NOT VERIFIED**. Windows behavior and multiline YAML frontmatter are also marked unverified in the repository map.

## Local checks

```bash
python3 -m unittest discover -s tests
python3 scripts/check_size.py
```

To test rendering in Chromium, install the optional dependencies and run `python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html`.
