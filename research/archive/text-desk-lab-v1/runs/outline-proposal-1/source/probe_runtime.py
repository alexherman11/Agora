"""Probe actual compiled runtime inventory using local mock inference, no live model."""

import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
from transport import INSTRUCTIONS,MODEL,TOOLS,runtime_config,thread_config
from openai_codex.client import CodexClient


def main():
    requests=[]
    class Model(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            assert not self.headers.get('Authorization')
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            output=[]
            if len(requests)==1:
                output=[{'type':'custom_tool_call','id':'ct1','call_id':'call1','name':'exec','namespace':'functions',
                         'input':'text({names:ALL_TOOLS.map(t=>t.name),globals:[typeof process,typeof fetch,typeof require],shell:typeof tools.exec_command,patch:typeof tools.apply_patch});'}]
            for item in output:self.emit({'type':'response.output_item.done','output_index':0,'item':item})
            self.emit({'type':'response.completed','response':{'id':f'r{len(requests)}','status':'completed','output':output,'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2}}})
        def emit(self,event):
            self.wfile.write(('data: '+json.dumps(event)+'\n\n').encode());self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Model)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix='text-desk-inventory-') as temp:
            with CodexClient(runtime_config(temp),approval_handler=lambda *_:{'decision':'decline'}) as client:
                timer=threading.Timer(50,client.close);timer.daemon=True;timer.start()
                try:
                    client.initialize()
                    config=thread_config(client)
                    config.update({'model_providers.probe':{'name':'Probe','base_url':f'http://127.0.0.1:{server.server_port}/v1','wire_api':'responses','requires_openai_auth':False,'supports_websockets':False},'features.enable_request_compression':False})
                    thread=client.thread_start({'model':MODEL,'modelProvider':'probe','config':config,'cwd':temp,'environments':[],
                        'selectedCapabilityRoots':[],'ephemeral':True,'approvalPolicy':'never','sandbox':'read-only',
                        'baseInstructions':INSTRUCTIONS,'developerInstructions':'','dynamicTools':TOOLS})
                    turn=client.turn_start(thread.thread.id,'Inspect only the runtime boundary.').turn.id
                    while True:
                        event=client.next_turn_notification(turn)
                        if event.method=='turn/completed':break
                finally:timer.cancel()
        assert len(requests)==2,len(requests)
        outputs=[i for i in requests[1]['input'] if i.get('type')=='custom_tool_call_output']
        text=outputs[0]['output']
        if isinstance(text,list):text='\n'.join(i.get('text','') for i in text)
        result,_=json.JSONDecoder().raw_decode(text[text.index('{"names"'):])
        assert set(result['names'])=={'look','act'},result
        assert result['globals']==['undefined']*3,result
        assert result['shell']==result['patch']=='undefined',result
        result.update(model=MODEL,kind='compiled runtime with mock inference; not a live model trial')
        (Path(__file__).parent/'runtime-inventory.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result))
    finally:server.shutdown();server.server_close()


if __name__=='__main__':main()
