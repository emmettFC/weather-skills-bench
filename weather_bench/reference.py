"""Trusted reference execution, isolated from evaluated agents."""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import shutil
from .catalog import ROOT, DEFAULT_CATALOG, lock, script_for, tree_hash
from .cases import cases, write_inputs, extract
from .grading import grade, workflow


def run_reference(catalog=DEFAULT_CATALOG):
    pin=lock(catalog)
    (ROOT/"catalog.lock.json").write_text(json.dumps(pin,indent=2)+"\n")
    out=ROOT/"results"; out.mkdir(exist_ok=True)
    reports=[]
    for case in (c for c in cases() if c.suite=='diagnostic-v2'):
        workspace=ROOT/".build"/"reference"/case.id
        if workspace.exists():
            shutil.rmtree(workspace)
        write_inputs(case,workspace)
        input_hashes={name:tree_hash(workspace/f"{name}.zarr") for name in case.datasets}
        start=time.monotonic(); events=[]; error=None
        for node in case.recipe:
            args=[]
            for name in node["inputs"]:
                args.extend(["--input",f"{name}.zarr"])
            if node["skill"]=="concat":
                args=["--input",*[f"{name}.zarr" for name in node["inputs"]]]
            args.extend(["--output",f"{node['output']}.zarr",*node["args"]])
            then=time.monotonic()
            proc=subprocess.run([sys.executable,str(script_for(node["skill"],catalog)),*args],cwd=workspace,capture_output=True,text=True,timeout=120)
            events.append({"action":"skill","skill":node["skill"],"args":args,"returncode":proc.returncode,
                           "seconds":time.monotonic()-then,"stderr":proc.stderr[-6000:].replace(str(ROOT),"$BENCHMARK")})
            if proc.returncode:
                error=proc.stderr[-6000:]; break
        actual=extract(case,workspace) if error is None else None
        score=grade(case.expected,actual)
        report={"case_id":case.id,"kind":"reference","answer":actual,"expected":case.expected,
                "correctness":score,"workflow":workflow(case,events),"wall_seconds":time.monotonic()-start,
                "input_sha256":input_hashes,"events":events,"error":error}
        reports.append(report)
        print(f"{case.id}: {'PASS' if score['passed'] else 'FAIL'} ({report['wall_seconds']:.2f}s)",flush=True)
        if error:
            print(error,flush=True)
        elif not score["passed"]:
            print(json.dumps({"actual":actual,"expected":case.expected,"failures":score["failures"]}),flush=True)
    existing=out/'reference.json'
    retained=[r for r in json.loads(existing.read_text())['runs'] if r['case_id'].startswith('e2e-')] if existing.exists() else []
    reports += retained
    result={"generated_at":datetime.now(timezone.utc).isoformat(),"kind":"reference_validation",
            "catalog_commit":pin["catalog_commit"],"core_commit":pin["core_commit"],"runs":reports}
    (out/"reference.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    public=ROOT/"cases"; public.mkdir(exist_ok=True)
    for case in (c for c in cases() if c.suite=='diagnostic-v2'):
        (public/f"{case.id}.json").write_text(json.dumps(case.public(),indent=2)+"\n")
    return result
