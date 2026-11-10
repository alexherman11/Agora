"""Door-level adversarial readings and edits; no browser, no model calls."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from painter.fixture import Fixture
from painter.install import Q,taskboard
from kernel.inpage import Principal


def main():
    f=Fixture();d=f.door;k=f.k;n=0
    def check(name,condition):
        nonlocal n
        assert condition,name;n+=1;print('PASS '+name,flush=True)
    def refused(line):return not d.request('/do',dict(line=line)).get('ok')
    try:
        member=k.join('proof:neighbour','Neighbour',invite={'admitted':True})['person']
        f.d.entry.sessions['peer']={'account':'proof:neighbour','method':'proof'}
        peer=taskboard.Door(f.url,'peer')
        private=d.say('make kind=secret sees=me title="A private reading"')['made'][0]
        public=d.say('make kind=lens name=secrets painter=components text='+Q('root : column, of tag:secret as item, each row\nrow : text "$item.title"'))['made'][0]
        check('View respects person visibility',private not in str(peer.say('look-view secrets')) and 'A private reading' in str(d.say('look-view secrets')))
        check('Only steward reviews component code',not peer.request('/do',dict(line='component '+f.ids['card'])).get('ok'))
        check('Ordinary set cannot forge component review',refused('set '+f.ids['card']+' reviewed_code=forged'))
        card=d.rows('component',name='card')[0];d.say('look '+card['id']);d.say('set '+card['id']+' code='+Q(card['code']+'\n// changed bytes'))
        changed=d.say('look-view taskboard-components plan=yes')['rows'][0]
        check('Changed module bytes enter quarantine before execution',all(p['health']['quarantined'] for p in changed['parts'] if p['component']=='card'))
        d.say('component '+card['id']);check('Explicit review restores description',d.say('look-view taskboard-components')['rows'][0]['counts']['card']==25)
        pref=d.say('make kind=view-preference sees=me lens=taskboard-components board-view.title="My board"')['made'][0]
        check('Personal setting applies only to maker','My board' in str(d.say('look-view taskboard-components')) and 'My board' not in str(peer.say('look-view taskboard-components')))
        check('Neighbour cannot overwrite private preference',not peer.request('/do',dict(line='set '+pref+' board-view.title=Other')).get('ok'))
        actor=k.actor_for(k.accounts['desktop:alex']);p=Principal(k,f.ids['taskboard-components'],actor,'contract')
        task=d.rows('taskboard-task')[0]
        check('Gesture principal cannot write a lens',not p.run('set '+public+' text=oops',saw={public:k.state.rev[public]}).get('ok'))
        check('Gesture principal can execute the composed task word',p.run('task-priority '+task['id']+' priority=2',saw={task['id']:task['rev']}).get('ok'))
        check('Stale painted task refuses',not p.run('task-priority '+task['id']+' priority=3',saw={task['id']:task['rev']}).get('ok'))
        node=d.say('look-view taskboard-components plan=yes')['rows'][0]['tree']['children'][0]['children'][0]['children'][0]
        # A receiving lane is a participant, even though task-move writes only a card.
        lane=d.rows('taskboard-lane')[0];task=d.rows('taskboard-task')[1]
        d.say('look '+lane['id']);d.say('set '+lane['id']+' name="Changed lane"')
        saw={task['id']:dict(rev=task['rev'],participant=True),lane['id']:dict(rev=lane['rev'],participant=True)}
        check('Stale receiving lane refuses too',not p.run('task-move '+task['id']+' to=Done',saw=saw).get('ok'))
        print(f'{n} of {n} contract checks passed',flush=True)
    finally:f.close()


if __name__=='__main__':main()
