"""Runtime-check receipts through the existing authenticated kernel door.

Only the record destination differs from WorldRecord. Checker, signing checks,
mock probes, publication journal, catalogs and authentication remain unchanged.
"""
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, ProxyHandler, build_opener

from runtime_pin import NoRedirect, PinRefused


class KernelRecord:
    def __init__(self, mcp):
        servers=json.loads(Path(mcp).read_text(encoding='utf-8'))['mcpServers']
        if set(servers)!={'agora'}:
            raise PinRefused('Kernel runtime records require exactly the existing Agora MCP server')
        env=servers['agora'].get('env',{})
        self.url=env.get('AGORA_URL','')
        self.token=env.get('AGORA_BEARER_TOKEN','')
        parsed=urlparse(self.url)
        if (parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost')
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('','/') or not self.token):
            raise PinRefused('Kernel runtime records need the existing authenticated loopback door')

    def __call__(self, kind, key, record):
        def quote(value):
            return '"'+str(value).replace('\\','\\\\').replace('"','\\"')+'"'
        source='codex-runtime-'+kind+'-'+key
        line='make kind=runtime-check name='+quote('Codex runtime '+kind)+' source='+quote(source)+' text='+quote(json.dumps(record,ensure_ascii=False))
        body=json.dumps({'line':line,'press':source}).encode()
        request=Request(self.url.rstrip('/')+'/do',body,
                        {'Content-Type':'application/json','Authorization':'Bearer '+self.token})
        with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=30) as reply:
            out=json.load(reply)
        if not out.get('ok'):
            raise PinRefused('Kernel refused runtime receipt; check retained local gate evidence')
