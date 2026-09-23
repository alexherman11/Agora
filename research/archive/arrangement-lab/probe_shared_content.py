"""Independent post-run shared-content probe, using each retained run's own adapter."""
import argparse
import importlib.util
import json
from pathlib import Path
import socket
import sys
import threading

ROOT = Path('C:/Projects/Agora/local/arrangement-trials-20260916')
parser = argparse.ArgumentParser()
parser.add_argument('label')
args = parser.parse_args()
folder = ROOT/'runs'/args.label
sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('retained_harness', folder/'live_trials.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
report = json.loads((folder/'report.json').read_text())
Gateway = h.Gateway
if report['arm'] == 'candidate':
    from native_arrangement import ArrangementGateway, SPECS
    Gateway = ArrangementGateway
    extra='\n'+''.join('allowed.add('+json.dumps(s['name'])+');' for s in SPECS)+'\n'
    h.server_module.FRAME=h.server_module.FRAME.replace('for(const method of [',extra+'for(const method of [',1)
h.server_module.Gateway=Gateway
with socket.socket() as s:
    s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
server, app=h.server_module.serve(folder/'world',port)
threading.Thread(target=server.serve_forever,daemon=True).start()
out=folder/'independent-content-probe';out.mkdir(exist_ok=False)
browser=h.Browser(out)
original=None
try:
    browser.call(op='open',url=f'http://127.0.0.1:{port}/#'+app.gateway.keep['operator'])
    browser.call(op='interact',action='resize',width=1900,height=1200)
    if report['arm']=='candidate':app.gateway.arrangements.browser=browser
    original=app.gateway.world.get('work-02')['facets']['core.text']
    obj=app.gateway.world.get('work-02')
    marker='INDEPENDENT SHARED CONTENT PROBE 20260916'
    app.gateway.commit(app.gateway.principal('human'),[{'id':'work-02','expected_revision':obj['revision'],
        'facets':{'core.text':{'text':original['text']+'\n\n'+marker}}}])
    observations={}
    if report['arm']=='candidate':
        for row in app.gateway.applications.list()['views']:
            if row['subject'] in ('oas-planning','oas-review'):
                observations[row['subject']]=browser.call(op='observe',view=row['id'],wait=3500,
                    selectors=['[data-occurrence]'],text_limit=20000)
        checks={'planning_two_occurrences_updated':observations['oas-planning']['text'].count(marker)==2,
                'review_updated':marker in observations['oas-review']['text']}
    else:
        for name,identity in [('Planning','oas.planning'),('Review','oas.review')]:
            browser.call(op='interact',action='click',name=name)
            config=app.gateway.world.get(identity)['facets']['core.collection']
            for entry in config['entries']:
                if entry['subject']=='work-02':
                    observations[entry['view']]=browser.call(op='observe',view=entry['view'],wait=1500,
                        selectors=['textarea','[contenteditable]'],text_limit=16000)
        checks={'all_three_occurrences_updated':len(observations)==3 and all(marker in json.dumps(o) for o in observations.values())}
    (out/'report.json').write_text(json.dumps({'checks':checks,'observations':observations},indent=2))
    print(json.dumps({'label':args.label,**checks}),flush=True)
finally:
    if original:
        obj=app.gateway.world.get('work-02')
        app.gateway.commit(app.gateway.principal('human'),[{'id':'work-02','expected_revision':obj['revision'],
            'facets':{'core.text':original}}])
    browser.close();server.shutdown();server.server_close();app.bridge.close()
