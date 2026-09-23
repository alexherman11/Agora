"""Combine the restored Agora4 design with the application's evidence and contracts."""
from pathlib import Path
import re

root=Path(r'C:\Projects\Agora\worlds\docs-restoration\repo')
pattern=r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> experiment/native-applications\n'
path=root/'DECISIONS.md'
path.write_text(re.sub(pattern,lambda m:m[1].rstrip()+'\n\n'+m[2],path.read_text(),flags=re.S),encoding='utf8')
path=root/'docs/Implementation Status.md'
text=path.read_text()
def status(match):
    ours=match[1]
    ours=ours[ours.index('This file is the evidence inventory'):]
    ours=ours.replace('No September 10 prose\nchange by itself advances the runtime status recorded below.',
                      'Documentation restoration alone does not advance runtime evidence;\nimplementation and checks are recorded separately below.')
    theirs=match[2]
    theirs=theirs[theirs.index('## Independent application branch'):]
    theirs=theirs.replace('## Independent application branch','## Agora4 integration')
    theirs=theirs.replace('`experiment/native-applications` preserves the combined improved-Desk runtime at\n`d8a7415` and adds independently installed Notes/Documents browser applications.',
        '`agora4` combines its restored design vault with the implementation from\n`experiment/native-applications` through `2a0e60a`, including the combined\nimproved-Desk runtime and independent Notes/Documents browser applications.')
    return '**Agora4 source, restored design and recorded evidence · September 10, 2026.**\n\n'+ours.rstrip()+'\n\n'+theirs
text=re.sub(pattern,status,text,flags=re.S)
path.write_text(text,encoding='utf8')
path=root/'docs/Start Here.md'
text=re.sub(pattern,lambda m:m[1],path.read_text(),flags=re.S)
needle='| [[Presentation and Operators]] | Retained visual intent, composition and actual interaction evidence |'
text=text.replace(needle,needle+'\n| [[Application Experiment]] | Independent Notes/Documents releases, shared objects and selections, per-view drafts, discussions and JEFF0 continuity; implemented on Agora4 |')
path.write_text(text,encoding='utf8')
assert not any(re.search(r'^<<<<<<<|^=======|^>>>>>>>',p.read_text(),re.M) for p in [root/'DECISIONS.md',root/'docs/Start Here.md',root/'docs/Implementation Status.md'])
print('Resolved three documentation conflicts; both design restoration and implementation evidence retained.')
