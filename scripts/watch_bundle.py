"""Refresh the portable HTML after each saved study result, then audit at completion.

This companion performs no model requests. It can run alongside weather_bench.monitor.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.bundle_dashboard import bundle


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study',type=Path)
    args=parser.parse_args();last=None
    while True:
        source=json.loads(args.study.read_text())
        public=json.loads((ROOT/'docs/data.json').read_text())
        study=next((s for s in public['studies'] if s['study_id']==source['study_id']),None)
        if study and len(study['runs'])==len(source['runs']) and bool(study.get('finished_at'))==bool(source.get('finished_at')):
            state=(len(study['runs']),bool(study.get('finished_at')))
            if state!=last:
                print(json.dumps(bundle(ROOT/'docs/weather-skills-benchmark.html')),flush=True);last=state
            if state[1]:
                subprocess.run([sys.executable,str(ROOT/'scripts/audit_study.py'),str(args.study.resolve())],cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT)},check=True)
                print('Final portable snapshot and integrity audit complete',flush=True)
                return
        time.sleep(5)

if __name__=='__main__':main()
