"""Teste visual de fumaça do viewer em Chromium sem GPU (SwiftShader).

Uso:
  pip install playwright pillow numpy && python3 -m playwright install chromium
  python3 tools/visual/smoke.py --html prototype/cerebro-semantico-3d.html --out shots/ [--vendor DIR] [--node NOME]

--vendor  pasta node_modules com three@0.160.0 e gsap@3.12.5 (npm i three@0.160.0 gsap@3.12.5).
          Sem ela, a página baixa as bibliotecas do CDN.
Grava visao-geral.png e ativo.png, mede a luminância de cada uma e sai com código 1 se a página
lançar erro. Em SwiftShader o FPS fica perto de 1: animação e física andam devagar, então espere
mais tempo antes de julgar um estado. Defeito visual só se declara com medição em tamanho real.
"""
import argparse
import asyncio
import os
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import measure  # noqa: E402

LIBS = {'cdn.jsdelivr.net/npm/three@0.160.0/': 'three', 'cdn.jsdelivr.net/npm/gsap@3.12.5/': 'gsap'}


def make_route(vendor):
    async def route(r):
        u = r.request.url
        if vendor:
            for prefix, pkg in LIBS.items():
                if prefix in u:
                    path = os.path.join(vendor, pkg, u.split(prefix)[1])
                    return await r.fulfill(path=path, content_type='application/javascript')
        if 'fonts.g' in u:
            return await r.abort()
        return await r.continue_()
    return route


async def main(a):
    os.makedirs(a.out, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader',
                                          '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': a.width, 'height': a.height})
        pg.on('pageerror', lambda e: errors.append(str(e)[:500]))
        await pg.route('**/*', make_route(a.vendor))
        await pg.add_init_script("window.addEventListener('DOMContentLoaded',()=>{ if(window.gsap) gsap.ticker.lagSmoothing(0) })")
        await pg.goto('file://' + os.path.abspath(a.html))
        await pg.wait_for_timeout(a.wait * 1000)
        await pg.evaluate("document.getElementById('fps').style.visibility='hidden'")
        print('stats:', await pg.inner_text('#stats'))
        shot1 = os.path.join(a.out, 'visao-geral.png')
        await pg.screenshot(path=shot1, timeout=120000)
        node = a.node or await pg.evaluate("document.querySelector('.label') && document.querySelector('.label').textContent")
        if node:
            ok = await pg.evaluate('(n) => CerebroSemantico.select(n)', node)
            await pg.wait_for_timeout(a.wait * 1000)
            shot2 = os.path.join(a.out, 'ativo.png')
            await pg.screenshot(path=shot2, timeout=120000)
            print('ativo:', node, '| select', ok)
        await b.close()
    box = [int(a.width * 0.26), int(a.height * 0.22), int(a.width * 0.79), int(a.height * 0.78)]
    for f in sorted(os.listdir(a.out)):
        if f.endswith('.png'):
            print(f, measure(os.path.join(a.out, f), box))
    if errors:
        print('ERROS NA PÁGINA:', errors[:5])
        return 1
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--html', required=True)
    ap.add_argument('--out', default='shots')
    ap.add_argument('--vendor', default=None)
    ap.add_argument('--node', default=None, help='nome do nó a ativar (padrão: o primeiro rótulo visível)')
    ap.add_argument('--wait', type=int, default=14, help='segundos de espera em cada estado')
    ap.add_argument('--width', type=int, default=1440)
    ap.add_argument('--height', type=int, default=900)
    sys.exit(asyncio.run(main(ap.parse_args())))
