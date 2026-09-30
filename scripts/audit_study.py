import json,sys
from pathlib import Path
from weather_bench.cases import cases
from weather_bench.grading import grade
from weather_bench.health import output_stem
path=Path(sys.argv[1]);s=json.loads(path.read_text());case_map={c.id:c for c in cases()};manifest=json.load(open('fixtures/manifest.json'))
assert len({r['run_id'] for r in s['runs']})==len(s['runs'])
assert len({(r['model'],r['case_id'],r['arm'],r['rep']) for r in s['runs']})==len(s['runs'])
for r in s['runs']:
 assert r['input_sha256']==manifest['cases'][r['case_id']]['stores'],r['run_id']
 case=case_map[r['case_id']]
 score=grade(case.expected,r['answer'],**case.public()['tolerance'])
 if case.suite=='end-to-end-v1':
  assert score==r['scientific_correctness'],r['run_id']
  if not r['figure']['passed']:score={'passed':False,'failures':score['failures']+['figure: required PNG delivery failed']}
  if r['status']=='source_changed':score={'passed':False,'failures':['Source version could not be verified after run']}
 assert score==r['correctness'],r['run_id']
 for key in ('prompt_tokens','completion_tokens','total_tokens'):
  assert r['usage'][key]==sum((q.get('usage') or {}).get(key,0) for q in r['requests']),r['run_id']
 assert abs(r['usage']['known_cost_usd']-sum((q.get('usage') or {}).get('cost',0) or 0 for q in r['requests']))<1e-9
 if r['arm']=='skills_only':
  assert set(r['image_ids'])=={'skills'},r['run_id']
  guides={}
  for e in r['events']:
   assert e['action']!='python',r['run_id']
   if e['action']=='read_skill':guides[e['skill']]=min(guides.get(e['skill'],999),e['turn'])
   if e['action']=='skill':assert guides.get(e['skill'],999)<e['turn'],r['run_id']
 else:assert set(r['image_ids'])=={'python'},r['run_id']
result={'study_id':s['study_id'],'recorded_attempts':len(s['runs']),'partial_trace_runs':[r['run_id'] for r in s['runs'] if r.get('recovery',{}).get('partial_trace')],'passed':True,'checks':['Unique isolated run IDs and task/model/condition cells','Fixture hashes match independent manifest','Saved answers independently regraded','Token and known cost totals reconcile to returned requests','Skills-only has no Python service or model code actions','Every recorded skill call follows an earlier recorded guide-read turn','Python baseline has no skills service']}
stem=output_stem(s['config'])
Path(f'results/{stem}-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if s['config'].get('retry_attempts'):
 from scripts.audit_provider_recovery import audit
 audit(s['study_id'])
