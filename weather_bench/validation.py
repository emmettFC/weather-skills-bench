"""Exercise every reference recipe inside the production evaluation sandbox."""
import json
from pathlib import Path
import shutil
from .catalog import ROOT, verify
from .cases import cases, write_inputs, extract
from .grading import grade, workflow
from .sandbox import Sandbox


def validate_containers():
    verify(); reports=[]
    for case in (c for c in cases() if c.suite=='diagnostic-v2'):
        folder=ROOT/".build"/"container-validation"/case.id
        if folder.exists(): shutil.rmtree(folder)
        write_inputs(case,folder/"inputs")
        events=[]
        with Sandbox(folder/"inputs",folder/"work",skills=True) as sandbox:
            check=sandbox.execute({"action":"python","code":
                "import os, importlib.util, pathlib, socket\n"
                "assert 'OPENROUTER_API_KEY' not in os.environ\n"
                "assert not pathlib.Path('/catalog').exists()\n"
                "assert importlib.util.find_spec('weather_skills_core') is None\n"
                "assert not pathlib.Path('/work/answer.json').exists()\n"
                "try:\n socket.create_connection(('1.1.1.1',443),timeout=.2)\n raise AssertionError('network enabled')\n"
                "except OSError: pass\nprint('Isolation checks passed')"})
            assert check["returncode"]==0,check
            for node in case.recipe:
                paths=[f"/inputs/{n}.zarr" if n in case.datasets else f"/work/{n}.zarr" for n in node["inputs"]]
                args=[part for path in paths for part in ("--input",path)]
                if node["skill"]=="concat": args=["--input",*paths]
                args.extend(["--output",f"/work/{node['output']}.zarr",*node["args"]])
                action={"action":"skill","skill":node["skill"],"args":args}
                event={**action,**sandbox.execute(action)}; events.append(event)
                if event["returncode"]: break
            actual=extract(case,folder/"work") if all(e["returncode"]==0 for e in events) else None
            report={"case_id":case.id,"correctness":grade(case.expected,actual),"workflow":workflow(case,events),"image_ids":sandbox.image_ids,"isolation_passed":True}
            reports.append(report)
            print(case.id, "PASS" if report["correctness"]["passed"] else "FAIL",flush=True)
            if not report["correctness"]["passed"]: print(json.dumps(events[-1]),flush=True)
    (ROOT/"results/container-validation.json").write_text(json.dumps(reports,indent=2)+"\n")
    if not all(r["correctness"]["passed"] and r["workflow"]["passed"] for r in reports):
        raise RuntimeError("Container validation failed")
    return reports


def validate_python():
    """Prove every task is solvable by one Python program without skills or feedback."""
    reports=[]
    source=(ROOT/"references/python_solutions.py").read_text()
    for case in (c for c in cases() if c.suite=='diagnostic-v2'):
        folder=ROOT/".build"/"python-validation"/case.id
        if folder.exists(): shutil.rmtree(folder)
        write_inputs(case,folder/"inputs")
        with Sandbox(folder/"inputs",folder/"work") as sandbox:
            event=sandbox.execute({"action":"python","code":f"CASE_ID={case.id!r}\n"+source})
            score=grade(case.expected,sandbox.answer())
            reports.append({"case_id":case.id,"correctness":score,"returncode":event["returncode"],"seconds":event["seconds"],"image_ids":sandbox.image_ids})
            print(case.id,'PASS' if score['passed'] else 'FAIL',flush=True)
            if not score['passed']: print(event,flush=True)
    (ROOT/"results/python-validation.json").write_text(json.dumps(reports,indent=2)+'\n')
    if not all(r['correctness']['passed'] for r in reports): raise RuntimeError('Python reference validation failed')
    return reports


def validate_skills_only():
    """Prove every answer can be submitted via skills + fixed artifact serialization."""
    verify(); reports=[]
    for case in (c for c in cases() if c.suite=='diagnostic-v2'):
        folder=ROOT/'.build/skills-only-validation'/case.id
        if folder.exists(): shutil.rmtree(folder)
        write_inputs(case,folder/'inputs'); events=[]
        with Sandbox(folder/'inputs',folder/'work',skills=True,skills_only=True) as sandbox:
            assert set(sandbox.containers)=={'skills'}
            try:
                sandbox.execute({'action':'python','code':'raise RuntimeError("must never run")'})
                raise AssertionError('Python was enabled')
            except ValueError: pass
            for node in case.recipe:
                paths=[f"/inputs/{n}.zarr" if n in case.datasets else f"/work/{n}.zarr" for n in node['inputs']]
                args=[part for path in paths for part in ('--input',path)]
                if node['skill']=='concat': args=['--input',*paths]
                args+=['--output',f"/work/{node['output']}.zarr",*node['args']]
                action={'action':'skill','skill':node['skill'],'args':args}
                event={**action,**sandbox.execute(action)};events.append(event)
                assert event['returncode']==0,event
            fields={}
            for key,spec in case.exports.items():
                if isinstance(spec,str): fields[key]=spec;continue
                store,variable=spec;fmt='values'
                if variable.startswith('@dates:'): fmt='dates';variable=variable.split(':')[1]
                if variable.startswith('@days:'): fmt='days';variable=variable.split(':')[1]
                fields[key]={'artifact':f'/work/{store}.zarr','variable':variable,'format':fmt}
            submitted=sandbox.submit_artifacts(fields)
            score=grade(case.expected,sandbox.answer())
            reports.append({'case_id':case.id,'correctness':score,'workflow':workflow(case,events),
                            'python_disabled':True,'submission_returncode':submitted['returncode'],'image_ids':sandbox.image_ids})
            print(case.id,'PASS' if score['passed'] else 'FAIL',flush=True)
            assert score['passed'],submitted
    (ROOT/'results/skills-only-validation.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports
