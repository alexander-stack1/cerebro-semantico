# Formato do grafo (BRAIN_DATA)

O viewer lê um objeto JSON. `pipeline/build_graph.py` gera esse objeto. `pipeline/embed_viewer.py` o grava na constante `BRAIN_DATA` da página. No navegador, `window.CerebroSemantico.setData(json)` troca o grafo sem recarregar.

## Exemplo mínimo

```json
{
  "categories": {
    "trabalho": { "label": "Trabalho", "color": "#4C8DFF", "lobe": "frontalE" },
    "casa":     { "label": "Casa",     "color": "#FFB547", "lobe": "limbico" }
  },
  "nodes": [
    { "id": "n000", "name": "Relatório mensal", "category": "trabalho", "weight": 0.9,
      "meta": "projeto · confiança alta", "act": [2, 0, 3],
      "connections": [ { "id": "n001", "proximity": 0.7 } ] },
    { "id": "n001", "name": "Reforma", "category": "casa", "weight": 0.5, "act": [0, 1, 0], "connections": [] }
  ],
  "source": "Minhas notas · 13/07 a 02/08/2026",
  "weeks": ["2026-07-13", "2026-07-20", "2026-07-27"],
  "until": "2026-08-02"
}
```

## Campos

| Campo | Obrigatório | Descrição |
|---|---|---|
| `categories` | sim | Mapa chave → `{label, color, lobe}`. `color` em `#RRGGBB`. |
| `categories.*.lobe` | não | Um de `frontalE`, `frontalD`, `parietalE`, `parietalD`, `temporalE`, `temporalD`, `limbico`, `posterior`. Sem ele, o viewer distribui na ordem. |
| `nodes[].id` | sim | Identificador único. |
| `nodes[].name` | sim | Rótulo exibido. Nunca nome de pessoa. |
| `nodes[].category` | sim | Chave de `categories`. |
| `nodes[].weight` | sim | 0 a 1. Importância visual quando não há linha do tempo. |
| `nodes[].connections` | sim | Lista de `{id, proximity}`. Proximidade de 0,1 a 1. Abaixo de 0,35 a conexão é latente. Pode ser declarada de um lado só; se aparecer dos dois, vale a maior. |
| `nodes[].meta` | não | Texto curto no painel do nó. |
| `nodes[].act` | com `weeks` | Registros por semana, alinhado com `weeks`. Com `weeks` e sem `act`, o nó fica frio. Sem `weeks`, o calor usa `weight`. |
| `source` | não | Texto no topo da página. Sem ele, aparece "dados de exemplo". |
| `weeks` | não | Segunda-feira de cada semana, em ordem. Sem ele, a linha do tempo some. |
| `until` | não | Último dia coberto (AAAA-MM-DD). |

## API no navegador

```js
CerebroSemantico.setData(json)   // reconstrói o grafo
CerebroSemantico.select(idOuNome) // ativa um nó
CerebroSemantico.reset()          // volta à visão geral
CerebroSemantico.destroy()        // libera WebGL, listeners e DOM
```
