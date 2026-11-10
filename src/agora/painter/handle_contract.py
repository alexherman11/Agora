"""Word-level adversarial checks for handles, observations and recovery."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.fixture import Fixture
from painter.install import Q,taskboard
from kernel.inpage import Principal
from kernel.kernel import Tx


def main():
    f=Fixture();d=f.door;k=f.k;n=0
    def check(name,ok):
        nonlocal n
        assert ok,name;n+=1;print('PASS '+name,flush=True)
    def refuse(line):return not d.request('/do',dict(line=line))['ok']
    try:
        style=d.say('make kind=part-style lens=taskboard-components target=card padding="2px 6px" glow="#abcd"')['made'][0]
        before=len(k.log.records);d.say('look '+style)
        check('Invalid style set changes no fact or record',refuse('set '+style+' glow="#12345"') and k.state.get(style,'glow')=='#abcd' and len(k.log.records)==before)
        check('CSS injection and excessive shorthand refuse',all(refuse('make kind=part-style lens=taskboard-components target=card '+s) for s in ('padding="1px 2px 3px 4px 5px"','color="red;display:none"','gap="-1px"','wat=red')))
        # An old invalid log value is possible even after new writes are guarded.
        with k.lock:
            tx=Tx(k);tx.part('legacy-style',style,'Legacy style fixture');tx.set(style,'padding','nonsense');k._commit(tx,by='kernel',words='legacy style fixture')
        p=d.say('look-view taskboard-components plan=yes')['rows'][0]
        check('Legacy paint-time style refusal is readable without losing the view',bool(p['style_errors']) and p['counts']['card']==25)
        d.say('make kind=part-style lens=taskboard-components target=tokens custom=9px motion-breathe='+Q(json.dumps({'from':{'opacity':0.5},'to':{'opacity':1},'duration':200})))
        d.say('personal-style taskboard-components target=card padding=custom')
        check('Personal style resolves shared tokens through a lens name or id',True)
        check('Unsafe motion tokens refuse',refuse('make kind=part-style lens=taskboard-components target=tokens motion-run='+Q('{"from":{"transform":"url(x)"}}')))
        # An agent is acting for Alex; maker identity differs from viewer identity.
        agent=taskboard.Door(f.url,f.d.entry.token('claude'))
        agent.say('personal-view taskboard-components board-view.title="Just mine"')
        check('Agent-created private preference applies to its person','Just mine' in str(d.say('look-view taskboard-components')))
        member=k.join('contract:another','Another',invite={'admitted':True})['person']
        f.d.entry.sessions['another']={'account':'contract:another','method':'proof'}
        peer=taskboard.Door(f.url,'another')
        check('Personal preference and paint refusals do not impersonate another viewer','Just mine' not in str(peer.say('look-view taskboard-components')))
        actor=k.actor_for(k.accounts['desktop:alex']);principal=Principal(k,f.ids['taskboard-components'],actor,'isolation-contract')
        part=next(p for p in d.say('look-view taskboard-components')['rows'][0]['parts'] if p['component']=='card')
        path=part['part'];lens=d.say('look-view taskboard-components')['rows'][0]['lens']
        data=Q(json.dumps([dict(path=path,health='stopped',last_error='Private failure text',elapsed_ms=10)]))
        records=len(k.log.records)
        for _ in range(2):assert principal.run('component-health '+lens+' data='+data)['ok']
        check('Repeated failures keep quarantine and component health on this screen',d.say('help card')['rows'][0]['quarantined'] and d.say('help card')['rows'][0]['health']=='stopped')
        # 26 Oct: paint health is screen state, kept in the kernel process's memory (painter/health.py), never the log
        check('Failure writes no record, no thing and no happening',len(k.log.records)==records and not k.things('paint-report') and k.happenings[-1]['word']!='component-health')
        check('Another viewer cannot read private failure text','Private failure text' not in str(peer.say('look-view taskboard-components')) and 'Private failure text' not in str(peer.say('rows paint-report')))
        out=peer.request('/do',dict(line='component-action '+lens+' path='+Q(path)+' action=clear'))
        check('Only a steward can clear quarantine',not out['ok'])
        assert principal.run('component-action '+lens+' path='+Q(path)+' action=clear')['ok']
        check('Steward clear resets the quarantine (on this screen)',not d.say('help card')['rows'][0]['quarantined'])
        card=d.rows('component',name='card')[0];original=card['code']
        d.say('look '+card['id']);d.say('set '+card['id']+' code='+Q("export default {mount(){throw Error('new version')}}"))
        fresh=d.rows('component',name='card')[0]
        stale=principal.run('component-action '+lens+' path='+Q(path)+' action=previous',saw={card['id']:card['rev']})
        check('Previous version refuses a concurrent or stale revision',not stale['ok'])
        previous=principal.run('component-action '+lens+' path='+Q(path)+' action=previous',saw={card['id']:fresh['rev']})
        check('Previous restores only the changed code field',previous['ok'] and k.state.get(card['id'],'code')==original)
        off=principal.run('component-action '+lens+' path='+Q(path)+' action=off')
        def disabled(tree):
            if tree['path']==path:return tree['disabled']
            return any(disabled(c) for c in tree['children'])
        plan=d.say('look-view taskboard-components plan=yes')['rows'][0]
        # 26 Oct: off is the viewer's own private preference (<part>.enabled=no): every instance of that part, for them only
        check("Turn off is this viewer's own preference for that part",off['ok'] and disabled(plan['tree']) and not disabled(peer.say('look-view taskboard-components plan=yes')['rows'][0]['tree']))
        d.say('make kind=component name=bad-metadata code="export default {}" settings="[]" parts="[]"')
        d.say('make kind=lens name=metadata-faults painter=components text='+Q('root : column\n  broken : bad-metadata\n  missing : absent-module\n  sibling : text "Still here"'))
        metadata=d.say('look-view metadata-faults')['rows'][0]['parts']
        check('Missing modules and malformed declarations stop their nodes, preserving siblings',sum(p['health']['health']=='stopped' for p in metadata)==2 and any(p['settings'].get('text')=='Still here' for p in metadata))
        print(f'{n} of {n} handle contract checks passed',flush=True)
    finally:f.close()


if __name__=='__main__':main()
