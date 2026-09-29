"""Descriptive intervals and paired tests; no model-as-judge or synthetic scores."""
import math
from collections import defaultdict
import numpy as np
from statistics import mean,median


def wilson(passed,total):
    if not total:return None
    z=1.959963984540054;p=passed/total;den=1+z*z/total
    center=(p+z*z/(2*total))/den
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return [max(0,center-radius),min(1,center+radius)]


def exact_mcnemar(skills_only,python_only):
    n=skills_only+python_only
    if not n:return 1.0
    return min(1.,2*sum(math.comb(n,k) for k in range(min(skills_only,python_only)+1))/2**n)


def condition_summary(runs, *, include_provider_errors=True):
    """Reproducible aggregates; operational by default, task outcomes on request."""
    groups=defaultdict(list)
    for run in runs:groups[(run['model'],run['arm'])].append(run)
    result=[]
    for (model,arm),all_runs in sorted(groups.items()):
        selected=[r for r in all_runs if r['status'] not in ('interrupted','source_changed') and (include_provider_errors or r['status']!='api_error')]
        if not selected:continue
        n=len(selected);passed=sum(r['correctness']['passed'] for r in selected)
        known=sum(r['usage']['known_cost_usd'] for r in selected)
        complete=all(r['usage']['cost_complete'] for r in selected)
        result.append({'model':model,'arm':arm,'recorded':len(all_runs),'scored':n,
                       'passed':passed,'success_rate':passed/n,'wilson_95':wilson(passed,n),
                       'median_seconds':median(r['solve_seconds'] for r in selected),
                       'mean_tokens':mean(r['usage']['total_tokens'] for r in selected),
                       'known_cost_usd':known,'cost_complete':complete,
                       'cost_per_attempt_usd':known/n if complete else None,
                       'cost_per_success_usd':known/passed if complete and passed else None,
                       'provider_errors':sum(r['status']=='api_error' for r in all_runs),
                       'protocol_rejections':sum(e['action']=='protocol_error' for r in selected for e in r['trace']),
                       'runs_using_skills':sum(any(e['action']=='skill' and '--help' not in (e.get('args') or []) for e in r['trace']) for r in selected),
                       'runs_reading_guides':sum(any(e['action']=='read_skill' for e in r['trace']) for r in selected)})
    return result


def paired_summary(runs,skill_arm='skills_only',family_size=None):
    indexed={(r['model'],r['case_id'],r['rep'],r['arm']):r for r in runs}
    reports=[]
    for model in sorted({r['model'] for r in runs}):
        pairs=[];excluded=0
        for (m,case,rep,arm),a in indexed.items():
            if m!=model or arm!=skill_arm:continue
            b=indexed.get((model,case,rep,'python'))
            if b is None:continue
            if a['status'] in ('api_error','interrupted','source_changed') or b['status'] in ('api_error','interrupted','source_changed'):excluded+=1;continue
            pairs.append((case,int(a['correctness']['passed']),int(b['correctness']['passed'])))
        by_case=defaultdict(list)
        for case,a,b in pairs:by_case[case].append(a-b)
        wins=sum(a>b for _,a,b in pairs);losses=sum(a<b for _,a,b in pairs)
        effects=[sum(v)/len(v) for v in by_case.values()]
        if not effects:continue
        rng=np.random.default_rng(20260929)
        boot=np.mean(rng.choice(effects,size=(10000,len(effects)),replace=True),axis=1)
        # McNemar's independent-pair assumption does not hold for repeated fixtures.
        independent=all(len(v)==1 for v in by_case.values())
        reports.append({'model':model,'pairs':len(pairs),'tasks':len(by_case),'excluded_provider_pairs':excluded,
                        'skills_only_wins':wins,'python_only_wins':losses,'both_pass':sum(a and b for _,a,b in pairs),
                        'both_fail':sum(not a and not b for _,a,b in pairs),
                        'success_difference':sum(effects)/len(effects),
                        'task_bootstrap_95':np.quantile(boot,[.025,.975]).tolist() if len(effects)>1 and len(set(effects))>1 else None,
                        'mcnemar_exact_p':exact_mcnemar(wins,losses) if independent else None,
                        'inference_note':'Exploratory; tasks are a fixed diagnostic set. Bootstrap resamples whole task effects and is omitted at degenerate boundaries. McNemar is omitted when fixtures repeat.'})
    eligible=sorted([r for r in reports if r['mcnemar_exact_p'] is not None],key=lambda r:r['mcnemar_exact_p'])
    previous=0
    for i,r in enumerate(eligible):
        previous=max(previous,min(1,r['mcnemar_exact_p']*((family_size or len(eligible))-i)))
        r['mcnemar_holm_p']=previous
    return reports
