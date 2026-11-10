"""Bounded pool policy, no live world or model."""
from unittest.mock import Mock, patch
from types import SimpleNamespace
import pytest
from test_builders import manager, msg, state

def configure(b, value=None, rows=None, failed=False):
    old=b.h.m.see
    data=rows if rows is not None else ([] if value is None else [dict(kind='house-settings',builder_capacity=value)])
    b.h.m.see=lambda line,*a,**kw: dict(ok=not failed,rows=data) if line=='rows house-settings' else old(line,*a,**kw)

def test_default_keeps_two(manager):
    configure(manager)
    assert manager.capacity==2

@pytest.mark.parametrize('value',[1,2,3,4,'3'])
def test_supported_pool_sizes(manager,value):
    configure(manager,value)
    assert manager.capacity==int(value)

@pytest.mark.parametrize('value',[0,5,-1,'many','3.0',True])
def test_bad_configuration_closes_admission(manager,value):
    configure(manager,value)
    with pytest.raises(RuntimeError,match='must be 1 to 4'):
        _=manager.capacity

def test_ambiguous_or_unavailable_settings_refuse(manager):
    configure(manager,rows=[dict(kind='house-settings'),dict(kind='house-settings')])
    with pytest.raises(RuntimeError,match='ambiguous'):_=manager.capacity
    configure(manager,failed=True)
    with pytest.raises(RuntimeError,match='unavailable'):_=manager.capacity

def test_three_requests_start_and_fourth_waits(manager):
    configure(manager,3)
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        for target in ('dk1','dk2','dk3'):
            assert manager.start(msg(target))['rows'][0]['doing']=='asked'
        assert 'starts by itself' in manager.start(msg('dk4'))['text']    # 4 Nov: it waits, never refused
        assert manager.states['dk4']['phase']=='queued'
        assert threads.Thread.call_count==3
        assert threads.Thread.return_value.start.call_count==3

def test_decrease_does_not_stop_existing_workers(manager):
    configure(manager,3)
    with patch('builders.threading', SimpleNamespace(Thread=Mock())):
        for target in ('dk1','dk2','dk3'):manager.start(msg(target))
    children={key:SimpleNamespace(stop=lambda:pytest.fail('active child stopped')) for key in manager.states}
    manager.children.update(children)
    configure(manager,1)
    assert manager.start(msg('dk4'))['rows'][0]['doing']=='queued'
    assert manager.children==children
    assert len(manager.states)==4


@pytest.mark.parametrize('phase,word',[('received','request_review'),('reviewed','land'),('received','land')])
def test_checks_and_landing_never_wait_on_worker_slots(manager,phase,word):
    configure(manager,1)                         # 4 Nov: landing is the House's own work, not a worker's slot
    target=state(manager,phase)
    manager.states['dk2']=dict(task='dk2',phase='working')
    with patch('builders.threading', SimpleNamespace(Thread=Mock())) as threads:
        result=getattr(manager,word)(msg())
        assert result.get('external'), result
        assert target['phase']=='reviewing'
        assert threads.Thread.call_count==1
