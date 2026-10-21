"""Deriva GIFs dos MP4s verificados. --check usa apenas a biblioteca padrão."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import demo_media

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = 'docs/media/animated-origin.json'
CLIPS = (('navegacao', 20), ('linha-do-tempo', 15))
INPUTS = ('docs/media/navegacao.mp4', 'docs/media/linha-do-tempo.mp4',
          'docs/media/origin.json', 'tools/visual/animated_preview.py')
OUTPUTS = tuple('docs/media/' + name + '.gif' for name, _ in CLIPS)
FILTER = ('[0:v]fps=4,scale=720:-1:flags=lanczos,split[a][b];'
          '[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=3')


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (*INPUTS, *OUTPUTS)}


def commands():
    return [['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-t', '30',
             '-i', 'docs/media/' + name + '.mp4', '-filter_complex', FILTER,
             '-loop', '0', 'docs/media/' + name + '.gif'] for name, start in CLIPS]


def check():
    receipt = json.loads((ROOT / RECEIPT).read_text())
    if receipt.get('sha256') != hashes():
        raise ValueError('Prévia ou origem diverge dos hashes')
    if receipt.get('commands') != commands() or not receipt.get('ffmpeg_version'):
        raise ValueError('Procedimento de geração ausente ou divergente')
    original = json.loads((demo_media.ROOT / demo_media.RECEIPT).read_text())
    demo_media.validate_metadata(original)
    if original['sha256'] != demo_media.hashes():
        raise ValueError('Origem dos MP4s mudou')
    for name in OUTPUTS:
        data = (ROOT / name).read_bytes()
        if data[:6] not in (b'GIF89a', b'GIF87a') or data[-1:] != b';':
            raise ValueError('GIF inválido')
    print('GIFs: hashes, fontes e procedimento OK')


def generate():
    demo_media.check()
    for command in commands():
        subprocess.run(command, cwd=ROOT, check=True)
        info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
            '-show_entries', 'stream=codec_name,width,height,nb_read_frames', '-of', 'json',
            command[-1]], cwd=ROOT, text=True))
        if info['streams'] != [{'codec_name': 'gif', 'width': 720, 'height': 450,
                                'nb_read_frames': '120'}]:
            raise ValueError('Prévia animada incompleta')
    receipt = {'commands': commands(), 'sha256': hashes(),
               'ffmpeg_version': subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0],
               'description': 'Trechos de 30 segundos, 4 quadros/s, 720x450; sem aceleração.'}
    (ROOT / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    check()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check() if args.check else generate()
