"""Check the recovery comparison against its original provider-failed panel."""
import argparse,json,sys,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from weather_bench.report import export_dashboard
from weather_bench.health import atomic_json
from scripts.bundle_dashboard import bundle


def audit(study_id):
    (ROOT/'.build').mkdir(exist_ok=True)
    with (ROOT/'.build/provider-recovery-audit.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return audit_locked(study_id)


def audit_locked(study_id):
    export_dashboard()
    data=json.loads((ROOT/'docs/data.json').read_text());by_id={s['study_id']:s for s in data['studies']}
    retry=by_id[study_id];view=by_id['repaired-'+study_id];base=by_id[retry['config']['comparison_parent']]
    old={r['run_id']:r for r in base['runs']};new={r['retry_of']['run_id']:r for r in retry['runs']}
    expected={rid for rid,r in old.items() if r['status']=='api_error'}
    assert set(new)<=expected and len(new)==len(retry['runs'])
    current={r['run_id']:r for r in view['runs']}
    for rid,r in old.items():
        if rid not in expected:assert current[rid]==r,'An original task outcome changed'
    for rid,r in new.items():assert current[r['run_id']]==r,'Replacement changed in comparison'
    assert {r['run_id'] for r in view['prior_provider_attempts']}==expected
    assert abs(view['ledger']['spent']-base['ledger']['spent']-retry['ledger']['spent'])<1e-8
    result={'study_id':study_id,'complete':bool(retry.get('finished_at')) and set(new)==expected,
            'original_provider_failures':len(expected),'retries_recorded':len(new),
            'remaining_provider_errors':sum(r['status']=='api_error' for r in retry['runs']),
            'retry_passes':sum(r['correctness']['passed'] for r in retry['runs']),
            'unchanged_task_outcomes':len(old)-len(expected),'reported_total_spend_usd':view['ledger']['spent'],
            'reported_retry_spend_usd':retry['ledger']['spent'],'passed':True,
            'checks':['Original non-provider outcomes unchanged','One designated replacement per provider-failed cell','Original failures remain linked','Total spend includes originals and retries']}
    atomic_json(ROOT/'results/provider-recovery-audit.json',result)
    bundle(ROOT/'docs/weather-skills-benchmark.html')
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('study_id');a=p.parse_args();audit(a.study_id)
