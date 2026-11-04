"""EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
needs something, the general form of it is the change.

Run existing scratch proofs sequentially and preserve each exact output."""
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent;LAB=HERE.parent;ROOT=LAB.parents[1]


def main():
    results=[]
    for name in ('byo_agent','council_night','hidden_hunt','kits','web_host','local_model'):
        target=HERE/'evidence'/('existing-'+name+'.txt')
        if name=='local_model':
            sys.path.insert(0,str(LAB.parents[0]/'window-lab/kernel-desktop'))
            from gaming_gate import assert_clear
            assert_clear()
        args=[sys.executable,str(LAB/'proof'/f'{name}.py')]
        with target.open('wb') as out:r=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT,cwd=ROOT,creationflags=0x08000000)
        results.append(dict(proof=name,exit=r.returncode));print(name,':',r.returncode,flush=True)
    (HERE/'evidence/existing-proofs.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return int(any(r['exit'] for r in results))


if __name__=='__main__':raise SystemExit(main())
