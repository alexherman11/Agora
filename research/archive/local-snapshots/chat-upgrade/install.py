"""Install the tested retained shell through the existing authenticated API."""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
world = Path('C:/Projects/Agora3/worlds/dev')
token = json.loads((world / 'keep.json').read_text())['operator']

def rpc(method, args=None):
    request = urllib.request.Request('http://127.0.0.1:8790/api/rpc',
        data=json.dumps({'method':method,'args':args or {}}).encode(),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=60) as response:
        result = json.load(response)
    if result.get('error'):
        raise RuntimeError(result['error'])
    return result['result']

assert not rpc('chat.status')['running'], 'JEFF is active; defer installation'
package = json.loads((ROOT / 'candidate.json').read_text())
current = rpc('package.get',{'id':'agora.shell'})
assert current['revision'] == package['revision'], 'Source changed; rebase and test'
source = package['facets']['agora.package']
installed = rpc('world.get',{'id':'agora.installation.agora.shell'})
rpc('package.save',{'id':'agora.shell','expected_revision':package['revision'], 'files':source['files'], 'manifest':source['manifest']})
build = rpc('package.build',{'id':'agora.shell','expected_revision':package['revision']+1})
result = rpc('package.install',{'id':'agora.shell','build':build['build'],'expected_revision':installed['revision']})
print(json.dumps({'source_revision':package['revision']+1,'installation_revision':result['items'][0]['revision']}))
