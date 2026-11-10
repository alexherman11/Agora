"""Package exact proof captures as before/after pairs; never opens a window."""
import hashlib
import html
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'evidence/ui';POLISH=OUT/'polish'
SCENES=['feed-catchup','kind-event','kind-poll','compose-event','search-results']


def main():
    proof=json.loads((OUT/'ui-proof.json').read_text(encoding='utf-8'))
    assert len(proof['screenshots'])==53 and all(c['ok'] for c in proof['checks'])
    pages=[];manifest=[]
    for scene in SCENES:
        for width in [1440,390]:
            source=OUT/f'{scene}-{width}.png'
            after=POLISH/f'{scene}-{width}-after.png';shutil.copyfile(source,after)
            before=POLISH/f'{scene}-{width}-before.png';assert before.exists()
            pages.append(f'<section><h2>{html.escape(scene)} · {width}px</h2><div class="pair">'+''.join(f'<figure><figcaption>{label}</figcaption><a href="{path.name}"><img src="{path.name}" alt="{label}: {html.escape(scene)} at {width} pixels"></a></figure>' for label,path in [('Before',before),('After',after)])+'</div></section>')
    for name in proof['screenshots']:
        path=HERE/name;manifest.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (POLISH/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Seabright polish comparison</title><style>body{font:16px system-ui;color:#303d37;background:#faf9f5;margin:24px}h1,h2{font-weight:600}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}figcaption{padding:8px 0}img{max-width:100%;height:auto;border:1px solid #cbdcd0}section{margin-bottom:40px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><h1>Seabright polish · before and after</h1>'+''.join(pages),encoding='utf-8')
    (POLISH/'capture-manifest.json').write_text(json.dumps(dict(screenshots=manifest,pairs=10,visual_review='Recorded separately after opening each final PNG.'),indent=2)+'\n',encoding='utf-8')
    print('POLISH CAPTURES: originals=53; before_after_pairs=10; extra_compose_chooser=2')


if __name__=='__main__':main()
