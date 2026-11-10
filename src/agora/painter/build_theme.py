"""Preserve the approved widget's visual theme as painter-owned theme tokens."""
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
source=(HERE.parent/'widgets/taskboard.js').read_text(encoding='utf-8')
theme=source.split('css(`',1)[1].split('`);',1)[0]
colours={}
def token(m):
    colour=m[0]
    if colour not in colours: colours[colour]='--board-colour-'+str(len(colours))
    return 'var('+colours[colour]+')'
theme=re.sub(r'#[0-9a-fA-F]{3,8}\b',token,theme)
tokens=':root{'+''.join(k+':'+v+';' for v,k in colours.items())+'}'
gallery='.catalogue{max-width:1200px;margin:auto}.catalogue>.gallery-example{margin:20px 0;padding:22px}.catalogue pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;max-height:180px;overflow:auto}.gallery-preview{max-height:360px;overflow:auto;border-top:1px solid var(--card);padding-top:16px}.gallery-example>[data-component=text]{font-size:16px;font-weight:600}.gallery-preview .lane{min-height:100px}'
(HERE/'theme.js').write_text('// First-party board theme; components use these tokens.\ncss(`'+gallery+'`);\ncss(`'+tokens+theme+'`);\n',encoding='utf-8')
