"""Mede a luminância de um screenshot numa caixa. Serve para julgar brilho por número, não por impressão.

Uso: python3 tools/visual/measure.py imagem.png [x0,y0,x1,y1]

Saída: média de luminância (0 a 255), % de pixels saturados (> 235), % acima de 180 e desvio local
médio (textura; perto de zero indica área chapada ou estourada). Referência medida em 1440x900 no
grafo real: visão geral com 3,3% saturado foi aceita; 23% foi tratado como estouro.
"""
import sys

import numpy as np
from PIL import Image


def measure(path, box=None):
    im = np.asarray(Image.open(path).convert('RGB')).astype(float)
    lum = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    x0, y0, x1, y1 = box or [380, 200, 1140, 700]
    r = lum[y0:y1, x0:x1]
    return {'media': round(float(r.mean())), 'saturado_pct': round(100 * float((r > 235).mean()), 1),
            'acima_180_pct': round(100 * float((r > 180).mean()), 1),
            'desvio_local': round(float(np.abs(np.diff(r, axis=1)).mean()), 2)}


if __name__ == '__main__':
    box = [int(v) for v in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    print(sys.argv[1], measure(sys.argv[1], box))
