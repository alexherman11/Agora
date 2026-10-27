"""Proof entry point. No default live mutation. --l0, --l1, --shadow SECONDS.
Evidence goes only under agora-wm/evidence (or --out).
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from engine import State, Window, Rect, solve
from simulator import render

HERE=Path(__file__).resolve().parent


def scenarios(out):
    replay={'state':{},'events':[]};s=State()
    for i,key in enumerate(['Terminal','Browser','Discord','Spotify','Editor','Agora board']):
        e={'type':'open','key':key,'window':{'preferred':[1250,900]}}
        replay['events'].append(e);s=solve(s,e).state
        render(s,out/f'day-{i+1}.png',f'A day of work: open {key}')
    (out/'day.replay.json').write_text(json.dumps(replay,indent=2))
    s=State(work=Rect(0,0,1800,1000))
    for i in range(5):s=solve(s,{'type':'open','key':f'App {i+1}','window':{'preferred':[850,700]}}).state
    render(s,out/'full.png','Full screen: oldest minimised')
    s=State(work=Rect(0,0,1800,1000),windows={
        'Pinned music':Window('Pinned music',rect=Rect(16,16,350,600),pinned=True)})
    for key in ('Browser','Terminal'):s=solve(s,{'type':'open','key':key,'window':{'preferred':[650,700]}}).state
    render(s,out/'pin.png','Pin stays fixed; new apps fit around it')
    s=State(work=Rect(0,0,2200,1000),windows={str(i+1):Window(str(i+1),rect=Rect(16+i*416,16,400,600)) for i in range(4)})
    render(s,out/'drag-before.png','Before drag across three neighbours')
    s=solve(s,{'type':'drag-end','key':'1','rect':[300,16,400,600]}).state
    render(s,out/'drag-after.png','After drag: connected neighbours pushed')
    s=State(work=Rect(0,0,2200,1400),windows={
        'Resize':Window('Resize',rect=Rect(16,16,600,400)),
        'Right':Window('Right',rect=Rect(632,16,500,600)),
        'Below':Window('Below',rect=Rect(16,432,600,400))})
    render(s,out/'resize-before.png','Before bottom-right corner resize')
    s=solve(s,{'type':'resize-end','key':'Resize','rect':[16,16,850,650]}).state
    render(s,out/'resize-after.png','Corner resize pushes right and below')
    for mode in ('fill','focus'):
        s=State(work=Rect(0,0,1800,1000),when_full=mode)
        s=solve(s,{'type':'open','key':'First','window':{'preferred':[900,700]}}).state
        s=solve(s,{'type':'open','key':'New','window':{'preferred':[1100,800]}}).state
        render(s,out/f'{mode}.png',f'when_full = {mode}')
    print('L0 scenarios: 14 PNGs + day.replay.json',flush=True)


def timing(out):
    rows=[]
    for count in (5,15,40):
        s=State(work=Rect(0,0,12000,8000),windows={str(i):Window(str(i),rect=Rect(16+(i%8)*1200,16+(i//8)*1000,1000,800)) for i in range(count)})
        samples=[]
        for i in range(200):
            start=time.perf_counter();solve(s,{'type':'drag-move','key':'0','rect':[100+(i%10),16,1000,800]})
            samples.append((time.perf_counter()-start)*1000)
        row={'windows':count,'median_ms':round(statistics.median(samples),3),'p95_ms':round(sorted(samples)[189],3),'max_ms':round(max(samples),3)}
        rows.append(row);print('L0 solve: '+json.dumps(row),flush=True)
    (out/'timing.json').write_text(json.dumps(rows,indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('--l0',action='store_true');p.add_argument('--l1',action='store_true')
    p.add_argument('--shadow',type=float);p.add_argument('--out',type=Path,default=HERE/'evidence');a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    if a.l0:
        subprocess.run([sys.executable,'-m','unittest','test_engine','-v'],cwd=HERE,check=True)
        scenarios(a.out);timing(a.out)
    if a.l1:
        from hidden_proof import run
        run(a.out)
    if a.shadow:
        from shadow import observe
        observe(a.shadow,a.out/'shadow.jsonl')


if __name__=='__main__':main()
