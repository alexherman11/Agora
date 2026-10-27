"""Privacy and date boundaries introduced by the polish pass; scratch only."""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'kernel-lab'))
from kernel.kernel import Kernel
from painter.handles import present


def test_private_vote_and_like_state(tmp_path):
    k=Kernel(tmp_path/'world',dict(tag='pl',name='Polish privacy',steward=dict(account='alex',name='Alex'),invites_counted_by='kernel',invites=[dict(code='x',uses=3)]))
    a=k.actor_for(k.accounts['alex']);b=k.actor_for(k.join('bea','Bea',invite='x')['person'])
    def act(who,line):
        out=k.run(who,line);assert out['ok'],out;return out
    post=act(a,'post title="A real choice" options="Saturday Sunday" text="Which day?"')['made'][0]
    act(a,'look '+post);act(a,'like '+post);act(a,'look '+post);act(a,'vote '+post+' Saturday')
    act(b,'look '+post);act(b,'vote '+post+' Sunday')
    first=k.shown(a.person,post);second=k.shown(b.person,post)
    assert first['you_liked'] is True and second['you_liked'] is False
    assert first['your_vote']=='Saturday' and second['your_vote']=='Sunday'
    assert first['votes']==second['votes']==2 and first['likes']==second['likes']==1
    assert not any(key.startswith(('vote:','like:')) for key in first.keys()|second.keys())


def test_initials_and_date_offsets():
    now=datetime(2026,10,26,18,tzinfo=timezone.utc)
    assert present('Neighbour 02','initials',now)=='N'
    assert present('','relative-date',now)==''
    assert present('Maya Lopez','initials',now)=='ML'
    assert present('Éva 123 Smith','initials',now)=='ÉS'
    assert present((now-timedelta(hours=2)).isoformat(),'short-relative',now)=='2h'
    assert present('2026-10-26T17:00:00+02:00','short-relative',now)=='3h'
    assert present('2026-10-22T12:00:00Z','short-relative',now)=='Thu'


def _rsvp_probe():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from proof import Proof,install,line
    f=Proof()
    try:
        ids=install(lambda x:f.say('Alex',x),lambda x:f.see('Alex',x))
        event=f.say('Alex',line('board.post',post_kind='event',start='2026-11-01T18:00:00Z',seats='3',text='Meet',**{'in':ids['channels']['Meetings & events']}))['made'][0]
        f.see('Alex','look '+event)
        f.say('Alex','board.rsvp '+event+' status=going')
        f.see('Alex','look '+event)
        f.say('Alex','board.rsvp '+event+' status=maybe')
        marker=f.see('Alex','rows board-rsvp')['rows']
        assert len(marker)==1 and marker[0]['status']=='maybe'
        assert next(row for row in f.see('Alex','rows post')['rows'] if row['id']==event)['seats_left']==2
    finally:f.close()


def test_rsvp_toggle_keeps_one_seat():
    # The broad suite has other legacy modules named "install". Keep this
    # integration world in its own interpreter, just like the board proofs.
    import subprocess
    pinned=Path(__file__).resolve().parents[3]/'.venv/Scripts/python.exe'
    result=subprocess.run([str(pinned),'-B',__file__,'--rsvp-probe'],capture_output=True,text=True,timeout=45)
    assert result.returncode==0,result.stdout+result.stderr


if __name__=='__main__' and '--rsvp-probe' in sys.argv:_rsvp_probe()
