import copy
import json
import pytest
from weather_bench.catalog import ROOT
from weather_bench.comparison import comparison_views,MODEL_OR_BATCH_KEYS
from weather_bench.health import output_stem


def study(name,model):
    return {'study_id':name,'config':{'models':[model],'cases':['a'],'arms':['skills_only','python'],'max_calls':40,'max_cost_usd':1,'providers':{model:['route']}},
            'planned_runs':2,'runs':[{'run_id':name+'1','model':model}],'catalog_commit':'pinned',
            'finished_at':None,'ledger':{'spent':.1},'health':{'state':'running'}}


def test_comparison_keeps_sources_and_sums_once():
    base=study('base','m1');extension=study('new','m2');extension['config']['extends_study']='base'
    original=copy.deepcopy([base,extension]);view=comparison_views([base,extension])[0]
    assert [base,extension]==original
    assert view['planned_runs']==4 and len(view['runs'])==2
    assert view['config']['models']==['m1','m2'] and view['ledger']['spent']==.2
    assert view['component_studies']==['base','new'] and view['runs'][1]['source_study_id']=='new'
    assert view['finished_at'] is None
    base['finished_at']='2026-09-29';extension['finished_at']='2026-09-30'
    assert comparison_views([base,extension])[0]['finished_at']=='2026-09-30'


@pytest.mark.parametrize('change',['budget','cases','catalog','model','run'])
def test_incompatible_or_duplicate_extension_rejected(change):
    base=study('base','m1');extension=study('new','m2');extension['config']['extends_study']='base'
    if change=='budget':extension['config']['max_calls']=41
    if change=='cases':extension['config']['cases']=['different']
    if change=='catalog':extension['catalog_commit']='different'
    if change=='model':extension['config']['models']=['m1']
    if change=='run':extension['runs'][0]['run_id']='base1'
    with pytest.raises(ValueError):comparison_views([base,extension])


def test_registered_ministral_settings_match_recovery():
    base=json.loads((ROOT/'configs/end-to-end-recovery-v2.json').read_text())
    new=json.loads((ROOT/'configs/end-to-end-ministral-v2.json').read_text())
    assert {k:v for k,v in base.items() if k not in MODEL_OR_BATCH_KEYS}=={k:v for k,v in new.items() if k not in MODEL_OR_BATCH_KEYS}
    assert len(new['models'])*len(new['cases'])*len(new['arms'])*new['repetitions']==6
    assert output_stem(new)=='ministral' and output_stem(base)=='e2e'
    assert new['models']==['mistralai/ministral-3b-2512']
    with pytest.raises(ValueError):output_stem({'output_stem':'../e2e'})
