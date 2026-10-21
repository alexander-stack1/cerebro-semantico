# Semantic Brain · Cérebro Semântico

[Português](README.md) | **English**

[![CI](https://github.com/alexander-stack1/cerebro-semantico/actions/workflows/ci.yml/badge.svg)](https://github.com/alexander-stack1/cerebro-semantico/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

> Turn WhatsApp messages into a history organized by topic, and explore its connections in an interactive 3D brain. This version is designed especially for workflows that feed messages collected through the WhatsApp API into a Markdown knowledge vault.

![Overview of the fictional example](docs/media/visao-geral.png)

API collection and message adaptation are handled by an external integration. This repository processes message excerpts, notes and graphs. It also works with Markdown notes from other sources. The interface and sample content remain in Portuguese; onboarding documentation is available in both languages.

## Contents

- [Build a history from WhatsApp](#build-a-history-from-whatsapp)
- [Quick start](#quick-start)
- [Gallery](#gallery)
- [Capabilities and limits](#capabilities-and-limits)
- [Documentation](#documentation)

## Build a history from WhatsApp

```text
WhatsApp API → external collection and adaptation → new messages in NDJSON
→ redacted excerpts by topic → notes updated by an external model
→ validation and timeline → graph → 3D brain
```

Conversations can feed a continuing history of projects, decisions, commitments and recurring topics. The consolidated history lives in Markdown notes. Dates make it possible to follow the activity of each topic week by week.

The project accepts messages that have already been collected and normalized. It does not connect an account to WhatsApp, receive webhooks on its own, or automatically retrieve earlier conversations. Collection, authentication, tracking processed messages and scheduling belong to the external integration. Updating notes through a model is also an external step, guided by the included briefing template.

**[Set up the WhatsApp history workflow →](docs/en/WHATSAPP.md)** · [How the graph works](docs/en/HOW_IT_WORKS.md)

## Quick start

Clone the repository and open the HTML file locally. GitHub's HTML file page shows source code; it does not run the application. The embedded graph is fictional. The browser needs internet access to load Three.js and GSAP from jsDelivr.

```bash
git clone https://github.com/alexander-stack1/cerebro-semantico.git
cd cerebro-semantico
open prototype/cerebro-semantico-3d.html  # macOS; on other systems, open the file in a browser
```

Drag to orbit, scroll to zoom, and click a neuron to select a topic. Press `Esc` to return to the overview and `/` to search. Use the timeline at the bottom right to move through the weeks.

To build a visualization from your own vault, use Python 3.9 or newer. The pipeline requires no external Python packages:

```bash
cp config/config.example.json config/config.json  # local file, ignored by Git
# Edit categories, vault.path, vault.folders and timeline.start.
python3 pipeline/build_graph.py --config config/config.json --out out/grafo.json --source "My notes"
python3 pipeline/embed_viewer.py --template prototype/cerebro-semantico-3d.html \
    --json out/grafo.json --out out/my-brain.html
```

The vault uses `.md` notes, simple `key: value` frontmatter, `[[Title]]` wikilinks and dated lines beginning with `- YYYY-MM-DD`. Categories and folders are configured in JSON. See [how it works](docs/en/HOW_IT_WORKS.md) and the [graph schema (Portuguese)](docs/FORMATO_GRAFO.md).

## Gallery

The screenshots show the overview, a selected topic and the timeline. The animated previews are 30-second excerpts from the actual recordings.

| Overview | Selected topic | Timeline |
|---|---|---|
| ![3D brain overview](docs/media/visao-geral.png) | ![Selected topic and connections](docs/media/tema-ativo.png) | ![Weekly timeline](docs/media/linha-do-tempo.png) |

| Navigation and search | Timeline playback |
|---|---|
| [![Animated navigation preview](docs/media/navegacao.gif)](https://github.com/alexander-stack1/cerebro-semantico/raw/refs/heads/main/docs/media/navegacao.mp4) | [![Animated timeline preview](docs/media/linha-do-tempo.gif)](https://github.com/alexander-stack1/cerebro-semantico/raw/refs/heads/main/docs/media/linha-do-tempo.mp4) |

**Full MP4s:** [download navigation and search · 1m27s](https://github.com/alexander-stack1/cerebro-semantico/raw/refs/heads/main/docs/media/navegacao.mp4) · [download timeline · 1m15s](https://github.com/alexander-stack1/cerebro-semantico/raw/refs/heads/main/docs/media/linha-do-tempo.mp4).

GitHub may not play an MP4 on its file page. These links access the files directly; if your browser downloads the video, open it in a local player. The GIF previews show motion within the README. While the repository is private, access requires an authorized account.

The media are real Chromium captures using SwiftShader software rendering, without audio. Frame rate is limited by the capture environment and does not measure GPU performance. [The source manifest](docs/media/origin.json) records provenance and hashes; verify it with `python3 tools/visual/demo_media.py --verify-ci`. The GIFs are derived from those MP4s; see [their manifest](docs/media/animated-origin.json).

## Capabilities and limits

- Direct connections come from wikilinks. Weaker latent connections come from shared excluded notes or tags. Node weight is based on its degree in the graph.
- Weekly activity has a three-week half-life: an earlier week's contribution halves over that interval. Latent links are calculated graph relationships, not AI-inferred connections.
- The viewer provides search, topic selection, category focus and a weekly timeline.
- Message tools prepare excerpts with known patterns redacted, validate notes and generate monthly timelines and event CSV files. Read the [English privacy guidance](docs/en/WHATSAPP.md#privacy) before processing real data.
- Redaction does not guarantee anonymization. Names in text, spelled-out identifiers, attachment contents and non-Brazilian formats may pass through. Review before sharing or sending excerpts to a model.
- The parser does not implement full YAML or multiline frontmatter. The viewer depends on a CDN. Chrome has been tested; Safari and Firefox are **NOT VERIFIED**.

## Documentation

- [WhatsApp history workflow](docs/en/WHATSAPP.md) · [Português](docs/WHATSAPP.md)
- [How it works](docs/en/HOW_IT_WORKS.md) · [Português](docs/COMO_FUNCIONA.md)
- [Capture scripts and reproduction (Portuguese)](docs/DEMONSTRACOES.md)
- [Graph schema (Portuguese)](docs/FORMATO_GRAFO.md)
- [Privacy details (Portuguese)](docs/PRIVACIDADE.md)
- [Repository map (Portuguese)](docs/agent/REPO_MAP.md)

The original still preview also has [a source manifest](docs/img/preview-origin.json). Verify it with `python3 tools/visual/preview.py --check --verify-ci`.

## Development

```bash
python3 -m unittest discover -s tests
python3 scripts/check_size.py
```

The pipeline and tests use the Python standard library. The optional visual smoke test needs Playwright, Pillow and NumPy: `python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html`.

## License

[MIT](LICENSE).
