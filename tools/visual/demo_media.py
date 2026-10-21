"""Captura o exemplo fictício: três PNGs e dois vídeos MP4, sem áudio.

python3 tools/visual/demo_media.py             # Playwright + Chromium + ffmpeg
python3 tools/visual/demo_media.py --check     # hashes locais + ffmpeg/ffprobe
python3 tools/visual/demo_media.py --verify-ci # também compara artefato remoto
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import preview

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = 'docs/media/origin.json'
INPUTS = tuple(dict.fromkeys((*preview.INPUTS, 'tests/test_build_graph.py',
    'tests/_util.py', 'tools/visual/demo_media.py', '.github/workflows/media.yml')))
OUTPUTS = tuple('docs/media/' + p for p in (
    'visao-geral.png', 'tema-ativo.png', 'linha-do-tempo.png',
    'navegacao.mp4', 'linha-do-tempo.mp4'))
REPO = 'alexander-stack1/cerebro-semantico'


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (*INPUTS, *OUTPUTS)}


def validate_video(path):
    if path.stat().st_size < 1024 or path.read_bytes()[4:8] != b'ftyp':
        raise ValueError('MP4 truncado ou inválido')
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-show_entries', 'stream=codec_name,width,height:format=duration',
        '-of', 'json', str(path)], text=True))
    if (info.get('streams') != [{'codec_name': 'h264', 'width': 1440, 'height': 900}]
            or not 10 <= float(info.get('format', {}).get('duration', 0)) <= 180):
        raise ValueError('Vídeo incompleto ou formato inesperado')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
                    '-f', 'null', '-'], check=True, capture_output=True)
    return info


def validate_metadata(receipt):
    observations = receipt.get('observations', {})
    expected = {p for p in OUTPUTS if p.endswith('.mp4')}
    if (not receipt.get('capture') or set(receipt.get('videos', {})) != expected
            or observations.get('selected') != 'Reforma do banheiro'
            or not observations.get('first_week') or not observations.get('middle_week')
            or observations['first_week'] == observations['middle_week']
            or not observations.get('stats')):
        raise ValueError('Metadados de captura incompletos')


def check(remote=False):
    receipt = json.loads((ROOT / RECEIPT).read_text())
    for key in ('revision', 'head_revision'):
        if not re.fullmatch('[0-9a-f]{40}', receipt.get(key, '')):
            raise ValueError('Revisão inválida')
    if not re.fullmatch('[0-9]+', receipt.get('ci_run') or ''):
        raise ValueError('Run de origem ausente')
    if receipt.get('sha256') != hashes():
        raise ValueError('Mídia ou fontes divergem dos hashes')
    validate_metadata(receipt)
    preview.check_example()
    for name in OUTPUTS:
        if name.endswith('.png'):
            preview.validate_png((ROOT / name).read_bytes())
        elif validate_video(ROOT / name) != receipt['videos'][name]:
            raise ValueError('Metadados do vídeo divergem')
    if remote:
        run = receipt['ci_run']
        info = json.loads(subprocess.check_output(
            ['gh', 'api', 'repos/' + REPO + '/actions/runs/' + run], text=True))
        if (info['status'], info['conclusion'], info['head_sha'], info['path']) != (
                'completed', 'success', receipt['head_revision'], '.github/workflows/media.yml'):
            raise ValueError('Run de origem não confere')
        with tempfile.TemporaryDirectory(prefix='cerebro-media-check-') as folder:
            subprocess.run(['gh', 'run', 'download', run, '--repo', REPO, '--name',
                            'demo-' + receipt['revision'], '--dir', folder], check=True)
            for name in (*OUTPUTS, RECEIPT):
                if (Path(folder) / Path(name).name).read_bytes() != (ROOT / name).read_bytes():
                    raise ValueError('Artefato remoto diverge')
    print('Mídia: fontes, hashes e formatos OK' + ('; artefato remoto OK' if remote else ''))


async def capture(folder):
    from playwright.async_api import async_playwright
    errors = []
    observations = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--use-angle=swiftshader',
            '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for scene in ('navegacao', 'linha-do-tempo'):
            context = await browser.new_context(viewport={'width': 1440, 'height': 900},
                record_video_dir=str(folder), record_video_size={'width': 1440, 'height': 900})
            page = await context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            await page.goto((ROOT / INPUTS[0]).as_uri())
            await page.wait_for_function('!!window.CerebroSemantico', timeout=120000)
            await page.locator('#stats').filter(has_text='40').wait_for(timeout=120000)
            await page.wait_for_timeout(14000)
            await page.locator('#fps').evaluate("el => el.style.visibility = 'hidden'")
            # O corte remove a carga inicial. A sequência restante conserva o tempo real.
            start = await page.evaluate('performance.now() / 1000')
            if scene == 'navegacao':
                await page.screenshot(path=str(ROOT / OUTPUTS[0]), timeout=120000)
                await page.wait_for_timeout(2500)
                await page.locator('#q').fill('Reforma')
                await page.wait_for_timeout(2000)
                await page.locator('#sugg button').filter(has_text='Reforma do banheiro').click()
                await page.locator('#panel.open').wait_for()
                await page.wait_for_timeout(7000)
                observations['selected'] = await page.locator('#panel h2').inner_text()
                if observations['selected'] != 'Reforma do banheiro':
                    raise ValueError('Tema inesperado')
                await page.screenshot(path=str(ROOT / OUTPUTS[1]), timeout=120000)
                await page.wait_for_timeout(3000)
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(5000)
            else:
                await page.locator('#tlBars button').first.click()
                observations['first_week'] = await page.locator('#tlLabel').inner_text()
                await page.wait_for_timeout(3000)
                await page.locator('#tlPlay').click()
                await page.wait_for_timeout(6500)
                await page.get_by_role('button', name='Pausar', exact=True).click()
                observations['middle_week'] = await page.locator('#tlLabel').inner_text()
                if observations['first_week'] == observations['middle_week']:
                    raise ValueError('Linha do tempo não avançou')
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(ROOT / OUTPUTS[2]), timeout=120000)
                await page.locator('#tlBars button').last.click()
                await page.wait_for_timeout(5000)
            observations['stats'] = await page.locator('#stats').inner_text()
            end = await page.evaluate('performance.now() / 1000')
            video = page.video
            await context.close()
            video_path = await video.path()
            # H.264, yuv420p e faststart para players de navegador. Sem áudio e sem acelerar.
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                '-ss', str(start), '-i', video_path, '-t', str(end - start),
                '-an', '-c:v', 'libx264', '-crf', '23', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', str(ROOT / 'docs/media' / (scene + '.mp4'))], check=True)
        await browser.close()
    if errors:
        raise ValueError('A página apresentou erros JavaScript')
    return observations


def generate():
    preview.check_example()
    subprocess.run(['python3', '-m', 'unittest', 'discover', '-s', 'tests',
                    '-p', 'test_build_graph.py'], cwd=ROOT, check=True)
    (ROOT / 'docs/media').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cerebro-demo-') as folder:
        observations = asyncio.run(capture(Path(folder)))
    probes = {}
    for name in OUTPUTS:
        if name.endswith('.mp4'):
            probes[name] = validate_video(ROOT / name)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    receipt = {'revision': revision, 'head_revision': os.environ.get('PREVIEW_HEAD_SHA', revision),
        'ci_run': os.environ.get('GITHUB_RUN_ID'), 'sha256': hashes(),
        'capture': 'Chromium SwiftShader, 1440x900, captura real sem áudio; carga inicial cortada',
        'observations': observations, 'videos': probes}
    (ROOT / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    check()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify-ci', action='store_true')
    args = parser.parse_args()
    check(args.verify_ci) if args.check or args.verify_ci else generate()
