import json
import sys
import urllib.request
from pathlib import Path

root=Path(r'C:\Projects\Agora\worlds\jeff0-desk')
keep=json.loads((root/'world/keep.json').read_text())
def rpc(method,args=None):
    req=urllib.request.Request('http://127.0.0.1:8873/api/rpc',data=json.dumps({'method':method,'args':args or {}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+keep['operator']})
    with urllib.request.urlopen(req,timeout=30) as response:
        value=json.load(response)
    if 'error' in value: raise RuntimeError(value['error'])
    return value['result']

if len(sys.argv)>1 and sys.argv[1]=='send':
    print(rpc('chat.send',{'message':Path(sys.argv[2]).read_text(encoding='utf8')}))
else:
    status=rpc('chat.status')
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps({'running':status['running'],'error':status['error'],'reply':status['reply'],'resident':status['resident'],'messages':len(status['messages']),'activity':status['activity']},ensure_ascii=True))
