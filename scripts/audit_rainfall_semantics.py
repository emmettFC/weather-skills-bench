"""Post-hoc sensitivity audit; never modifies registered answers or model scores.

The task does not specify clipping of negative daily increments. Compare the
registered clipped-increment oracle with direct cumulative endpoint differences.
Both use the same raw archives, periods, domain and ensemble statistics.
"""
import json
import sys
from pathlib import Path
import numpy as np
from references.e2e.oracle import raw,area,restore_sources,calculate
from weather_bench.grading import grade
from weather_bench.cases import cases
from weather_bench.health import atomic_json


def endpoint_answers():
    answers=calculate()
    def weeks(name):
        ds,a,lat,lon=raw(name,'tp')
        lead=(ds.step.values/np.timedelta64(1,'D')).astype(int)
        indices=[int(np.flatnonzero(lead==day)[0]) for day in range(0,43,7)]
        return np.diff(a.astype(float)[:,indices],axis=1),lat
    a,lat=weeks('rain-current');b,_=weeks('rain-previous');region=area(a,lat)
    rain=answers['e2e-kenya-rainfall']
    rain.update(ensemble_mean_mm=a.mean(axis=0).tolist(),regional_median_mm=np.median(region,axis=0).tolist(),regional_spread_mm=region.std(axis=0,ddof=1).tolist())
    current=a[:,:2].mean(axis=0);previous=b[:,1:3].mean(axis=0);delta=current-previous
    answers['e2e-kenya-revision'].update(current_mean_mm=current.tolist(),previous_mean_mm=previous.tolist(),change_mm=delta.tolist(),regional_change_mm=area(delta[None],lat)[0].tolist())
    return {k:v for k,v in answers.items() if k!='e2e-kenya-heat'}


def audit(study_path):
    restore_sources();alternate=endpoint_answers();case_map={c.id:c for c in cases()};s=json.loads(Path(study_path).read_text());rows=[]
    for r in s['runs']:
        if r['case_id'] not in alternate:continue
        score=grade(alternate[r['case_id']],r['answer'],**case_map[r['case_id']].public()['tolerance'])
        rows.append({'run_id':r['run_id'],'model':r['model'],'arm':r['arm'],'case_id':r['case_id'],'status':r['status'],'registered_passed':r['correctness']['passed'],'endpoint_scientific_passed':score['passed'],'endpoint_delivery_passed':score['passed'] and r.get('figure',{}).get('passed',False)})
    result={'study_id':s['study_id'],'kind':'post-hoc-sensitivity-audit','changes_registered_scores':False,'issue':'Rainfall briefs do not specify clipping negative daily precipitation increments. The registered oracle clips; cumulative endpoint subtraction is also consistent with the brief. Interpret rainfall failures with this ambiguity in mind.','affected_cases':list(alternate),'runs':rows}
    atomic_json(Path('results/rainfall-semantics-audit.json'),result)
    print(json.dumps({'audited':len(rows),'alternate_only_passes':[r['run_id'] for r in rows if r['endpoint_delivery_passed'] and not r['registered_passed']]}))

if __name__=='__main__':audit(sys.argv[1])
