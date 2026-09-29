"""Validate real-source cases against independent raw-data answers, then freeze briefs."""
import base64
from datetime import datetime,timezone
import json
import shutil
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request
from .catalog import ROOT,verify
from .e2e_cases import e2e_cases
from .e2e_sandbox import E2ESandbox
from .grading import grade,workflow


def check_sources(case):
    manifest=json.loads((ROOT/'fixtures/real-sources.json').read_text())
    urls={v for k,v in case.expected.items() if k.endswith('source_url')}
    checked={}
    for name,entry in manifest.items():
        if entry['url'] not in urls:continue
        prefix=entry['url'].split('/kenya-forecasting-data/',1)[1]+'/'
        endpoint='https://storage.googleapis.com/storage/v1/b/kenya-forecasting-data/o?'+urllib.parse.urlencode({'prefix':prefix,'maxResults':1000})
        listing=json.load(urllib.request.urlopen(endpoint,timeout=60))
        assert not listing.get('nextPageToken'),'Source needs paginated version check'
        actual={x['name'][len(prefix):]:x['generation'] for x in listing.get('items',[])}
        expected={x['path']:x['generation'] for x in entry['objects']}
        if actual!=expected:raise ValueError(f'Archived source changed: {name}; do not score against stale ground truth')
        checked[name]={'objects':len(actual),'version_match':True}
    assert len(checked)==len(urls)
    return checked


def collect_figure(sandbox,destination):
    # Resolve and read in the container: never follow an agent-created host link.
    code="""import base64,json
from pathlib import Path
from PIL import Image,ImageStat
p=Path('/work/outlook.png').resolve()
assert p.is_relative_to('/work') and p.stat().st_size < 10000000
with Image.open(p) as im:
 assert im.format=='PNG' and im.width>=400 and im.height>=250
 assert max(ImageStat.Stat(im.convert('RGB')).stddev)>2
 print(json.dumps({'width':im.width,'height':im.height,'png':base64.b64encode(p.read_bytes()).decode()}))
"""
    target=next(iter(sandbox.containers.values()))
    p=subprocess.run(['docker','exec',target,'python','-c',code],capture_output=True,text=True,timeout=30)
    if p.returncode:return {'passed':False,'reason':'Missing, unreadable, blank or undersized outlook.png'}
    data=json.loads(p.stdout);dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(base64.b64decode(data.pop('png')))
    return {'passed':True,**data,'scope':'PNG delivery only; visual scientific correctness is not automatically graded'}


def fields(case):
    out={}
    for key,spec in case.exports.items():
        if isinstance(spec,str):out[key]=spec;continue
        store,var=spec;fmt='values'
        if var.startswith('@dates:'):fmt='dates';var=var.split(':')[1]
        if var.startswith('@days:'):fmt='days';var=var.split(':')[1]
        out[key]={'artifact':'/work/'+store+'.zarr','variable':var,'format':fmt}
    return out


def run():
    pin=verify();reports=[]
    for case in e2e_cases():
        check_sources(case)
        folder=ROOT/'.build/e2e-reference'/case.id
        if folder.exists():shutil.rmtree(folder)
        (folder/'inputs').mkdir(parents=True,exist_ok=True)
        events=[];started=time.monotonic()
        with E2ESandbox(folder/'inputs',folder/'work',skills=True,skills_only=True) as s:
            for node in case.recipe:
                paths=['/work/'+n+'.zarr' for n in node['inputs']]
                args=[part for p in paths for part in ('--input',p)]
                filename=node['output'] if node['output'].endswith('.png') else node['output']+'.zarr'
                args+=['--output','/work/'+filename,*node['args']]
                event={'action':'skill','skill':node['skill'],'args':args}
                event.update(s.execute(event,timeout=180));events.append(event)
                print(case.id,node['id'],event['returncode'],round(event['seconds'],1),flush=True)
                if event['returncode']:print(event['stderr'],flush=True);break
            actual=None
            if all(e['returncode']==0 for e in events):
                result=s.submit_artifacts(fields(case))
                if result['returncode']:print(result,flush=True)
                actual=s.answer()
            score=grade(case.expected,actual,atol=1e-4)
            figure=collect_figure(s,ROOT/'docs/artifacts/reference'/f'{case.id}.png')
            images=s.image_ids
        check_sources(case)
        report={'case_id':case.id,'kind':'reference','answer':actual,'expected':case.expected,'correctness':score,'workflow':workflow(case,events),'figure':figure,'wall_seconds':time.monotonic()-started,'events':events,'network_events':s.network_events,'image_ids':images,'input_sha256':{},'error':None if score['passed'] else score['failures']}
        reports.append(report);print(case.id,'PASS' if score['passed'] and figure['passed'] else 'FAIL',score['failures'],flush=True)
        # The Python witness is independent of catalog implementations and
        # retrieves the same raw provider stores in a fresh empty sandbox.
        python_folder=ROOT/'.build/e2e-python-reference'/case.id
        if python_folder.exists():shutil.rmtree(python_folder)
        (python_folder/'inputs').mkdir(parents=True,exist_ok=True)
        source=(ROOT/'references/e2e/python_solution.py').read_text()
        with E2ESandbox(python_folder/'inputs',python_folder/'work') as p:
            event=p.execute({'action':'python','code':f'CASE_ID={case.id!r}\n'+source},timeout=240)
            actual=p.answer();score=grade(case.expected,actual,atol=1e-4)
            png=collect_figure(p,ROOT/'docs/artifacts/reference'/f'{case.id}-python.png')
        report['python_reference']={'answer':actual,'correctness':score,'figure':png,'event':event,'image_ids':p.image_ids,'network_events':p.network_events}
        report['oracle_verified']=score['passed'] and png['passed']
        print(case.id,'Python PASS' if report['oracle_verified'] else 'Python FAIL',event['stderr'][-1500:] if not report['oracle_verified'] else '',flush=True)
    output={'generated_at':datetime.now(timezone.utc).isoformat(),'catalog_commit':pin['catalog_commit'],'core_commit':pin['core_commit'],'runs':reports}
    (ROOT/'results/e2e-reference.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    if not all(r['oracle_verified'] for r in reports):raise RuntimeError('Independent E2E validation failed')
    path=ROOT/'results/reference.json';old=json.loads(path.read_text());ids={r['case_id'] for r in reports}
    old['runs']=[r for r in old['runs'] if r['case_id'] not in ids]+reports
    path.write_text(json.dumps(old,indent=2,allow_nan=False)+'\n')
    for case in e2e_cases():(ROOT/'cases'/f'{case.id}.json').write_text(json.dumps(case.public(),indent=2)+'\n')
    return output

if __name__=='__main__':run()
