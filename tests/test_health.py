import json
import os
import time
from datetime import datetime, timezone
from weather_bench import health


def study():
    return {'study_id':'test','runs':[],'planned_runs':2}


def test_unfinished_study_without_heartbeat_is_stopped(tmp_path, monkeypatch):
    monkeypatch.setattr(health,'ROOT',tmp_path)
    assert health.study_health(study())['state']=='stopped'


def test_live_stale_and_dead_heartbeats(tmp_path, monkeypatch):
    monkeypatch.setattr(health,'ROOT',tmp_path)
    now=time.time()
    path=tmp_path/'results/health/test.json'
    data={'pid':os.getpid(),'state':'running','updated_at':datetime.fromtimestamp(now,timezone.utc).isoformat(),'active':{'case_id':'rain'}}
    health.atomic_json(path,data)
    assert health.study_health(study(),now=now)['state']=='running'
    assert health.study_health(study(),now=now+31)['state']=='stopped'
    def dead(pid, signal):raise ProcessLookupError()
    monkeypatch.setattr(health.os,'kill',dead)
    assert health.study_health(study(),now=now)['state']=='stopped'


def test_heartbeat_finishes_and_exception_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(health,'ROOT',tmp_path)
    with health.heartbeat('test') as update:
        update(active={'case_id':'rain'})
        assert health.study_health(study())['active']['case_id']=='rain'
    path=tmp_path/'results/health/test.json'
    assert json.loads(path.read_text())['state']=='finished'
    try:
        with health.heartbeat('test'):
            raise RuntimeError('worker failed')
    except RuntimeError:
        pass
    assert json.loads(path.read_text())['state']=='stopped'
    assert health.study_health(study())['state']=='stopped'


def test_completion_uses_coverage_not_heartbeat():
    s={**study(),'finished_at':'2026-09-29T00:00:00Z'}
    assert health.study_health(s)['state']=='partial'
    s['runs']=[{},{}]
    assert health.study_health(s)['state']=='complete'


def test_provider_only_group_is_not_zero_capability():
    from weather_bench.statistics import condition_summary
    run={'model':'m','arm':'python','status':'api_error','correctness':{'passed':False},
         'usage':{'known_cost_usd':0.,'cost_complete':True,'total_tokens':0},'solve_seconds':1.,'trace':[]}
    assert condition_summary([run])[0]['success_rate']==0
    assert condition_summary([run],include_provider_errors=False)==[]
    passed={**run,'status':'submitted','correctness':{'passed':True},'solve_seconds':10.}
    result=condition_summary([run,passed],include_provider_errors=False)[0]
    assert result['recorded']==2 and result['scored']==1 and result['success_rate']==1
    assert result['median_seconds']==10
    assert result['provider_errors']==1
