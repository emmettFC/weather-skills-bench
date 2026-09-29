"""Tests for real-source boundaries, answer reproducibility, and scientific traps."""
import copy
import importlib.util
import json
from pathlib import Path
import numpy as np
from weather_bench.catalog import ROOT
from weather_bench.cases import cases
from weather_bench.grading import grade
from weather_bench.runner import prompt
from weather_bench.queued_study import dependency_finished


def oracle():
    spec=importlib.util.spec_from_file_location('real_oracle',ROOT/'references/e2e/oracle.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.restore_sources()
    return module


def test_real_answers_recompute_from_hash_checked_raw_snapshots():
    calculated=oracle().calculate()
    for case in cases():
        if case.suite=='end-to-end-v1':assert grade(case.expected,calculated[case.id],**case.public()['tolerance'])['passed']


def test_same_lead_forecast_comparison_is_detectably_wrong():
    module=oracle();current,_,_=module.weekly('rain-current');previous,_,_=module.weekly('rain-previous')
    case=next(c for c in cases() if c.id=='e2e-kenya-revision')
    wrong=copy.deepcopy(case.expected)
    wrong['change_mm']=(current[:,:2].mean(axis=0)-previous[:,:2].mean(axis=0)).tolist()
    assert not grade(case.expected,wrong,**case.public()['tolerance'])['passed']


def test_local_peak_then_spatial_mean_is_not_regional_peak():
    module=oracle();_,values,lat,_=module.raw('temperature','t2m')
    local=values[:,:14].astype(float).reshape(101,2,7,len(lat),values.shape[-1]).max(axis=2)-273.15
    wrong=module.area(local,lat)
    case=next(c for c in cases() if c.id=='e2e-kenya-heat')
    answer=copy.deepcopy(case.expected);answer['median_peak_c']=np.median(wrong,axis=0).tolist()
    assert not grade(case.expected,answer,**case.public()['tolerance'])['passed']


def test_fetch_normalization_cannot_be_replaced_with_cumulative_weekly_sum():
    module=oracle();_,values,_,_=module.raw('rain-current','tp')
    case=next(c for c in cases() if c.id=='e2e-kenya-rainfall')
    wrong=copy.deepcopy(case.expected)
    wrong['ensemble_mean_mm']=np.stack([values[:,i+1:i+8].sum(axis=1).mean(axis=0) for i in range(0,42,7)]).tolist()
    assert not grade(case.expected,wrong,**case.public()['tolerance'])['passed']


def test_real_briefs_have_no_synthetic_metadata_or_private_recipe():
    for case in cases():
        if case.suite!='end-to-end-v1':continue
        public=case.public()
        assert not case.datasets and public['inputs']==[]
        assert not {'challenge','input_metadata','recipe','expected'} & public.keys()
        assert public['source_notes'] and 'real archived forecasts' in public['fixture_kind']
    assert 'kenya-forecast-fetch' in prompt('skills_only',network=True)
    assert '"name": "kenya-forecast-fetch"' not in prompt('skills_only')
    assert 'Network access is disabled.' not in prompt('python',network=True)


def test_queued_study_waits_for_actual_completion(tmp_path):
    path=tmp_path/'queue.json';path.write_text(json.dumps({'state':'waiting'}));assert not dependency_finished(path)
    path.write_text(json.dumps({'state':'running'}));assert not dependency_finished(path)
    path.write_text(json.dumps({'state':'complete'}));assert dependency_finished(path)


def test_recipe_accepts_different_figure_wording_but_requires_artifact_ancestry():
    from weather_bench.grading import workflow
    case=next(c for c in cases() if c.id=='e2e-kenya-revision')
    events=[]
    for n in case.recipe:
        args=[p for name in n['inputs'] for p in ('--input',name+'.zarr')]+['--output',n['output']+'.zarr',*n['args']]
        events.append({'action':'skill','skill':n['skill'],'returncode':0,'args':args})
    plot=events[-1]['args'];plot[plot.index('--title')+1]='Different accurate briefing title'
    plot[plot.index('--colormap')+1]='RdBu'
    assert workflow(case,events)['passed']
    plot[plot.index('--input')+1]='unrelated.zarr'
    assert not workflow(case,events)['passed']
