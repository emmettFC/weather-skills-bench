"""Run a prespecified experiment after its study or queue dependency completes."""
import json
import subprocess
import sys
import time
from pathlib import Path
from .catalog import ROOT


def dependency_finished(path):
    try:
        data=json.loads(path.read_text())
        if data.get('state') in ('failed','blocked'):raise RuntimeError('Preceding queued study failed; inspect its log before continuing')
        return bool(data.get('finished_at')) or data.get('state') in ('complete','partial')
    except json.JSONDecodeError:
        return False


def main():
    after=Path(sys.argv[1]).resolve();config=Path(sys.argv[2]).resolve()
    spec=json.loads(config.read_text())
    role=spec.get('study_role')
    if role not in ('small-model-extension','end-to-end'):
        raise ValueError('Unknown queued study role')
    stem='e2e' if role=='end-to-end' else 'small-model'
    state_path=ROOT/f'results/{stem}-queue.json'
    state={'state':'waiting','after_study':after.stem,'config':str(config.relative_to(ROOT)),
           'models':spec['models'],'planned_attempts':len(spec['models'])*len(spec['cases'])*len(spec['arms'])*spec['repetitions'],
           'max_cost_usd':spec['max_cost_usd']}
    def save():
        state_path.write_text(json.dumps(state,indent=2)+'\n')
    save();print(stem+' study queued after '+after.stem,flush=True)
    while True:
        try:ready=dependency_finished(after)
        except RuntimeError as exc:
            state.update(state='blocked',reason=str(exc));save();return
        if ready:break
        time.sleep(5)
    before=set((ROOT/'results/studies').glob('*.json'))
    with (ROOT/f'.build/{stem}-study.log').open('w') as log:
        process=subprocess.Popen([sys.executable,'-m','weather_bench.cli','study','--config',str(config),*(['--resume',sys.argv[3]] if len(sys.argv)>3 else [])],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        state.update(state='starting',pid=process.pid);save();study_path=None
        while process.poll() is None and study_path is None:
            for path in set((ROOT/'results/studies').glob('*.json'))-before:
                try:data=json.loads(path.read_text())
                except json.JSONDecodeError:continue
                if data['config'].get('study_role')==role:study_path=path;break
            if study_path is None:time.sleep(1)
        monitor=None;monitor_log=None
        if study_path:
            state.update(state='running',study_id=study_path.stem);save()
            monitor_log=(ROOT/f'.build/{stem}-monitor.log').open('w')
            monitor=subprocess.Popen([sys.executable,'-m','weather_bench.monitor',str(study_path)],cwd=ROOT,stdout=monitor_log,stderr=subprocess.STDOUT)
        code=process.wait()
        if monitor:
            if code:monitor.terminate()
            try:monitor_code=monitor.wait(timeout=120)
            except subprocess.TimeoutExpired:
                monitor.terminate();monitor_code=1
            monitor_log.close()
        else:monitor_code=1
        if study_path and not code:
            data=json.loads(study_path.read_text());state['recorded_attempts']=len(data['runs'])
            state['state']='complete' if len(data['runs'])==data['planned_runs'] else 'partial'
        else:state['state']='failed'
        state.update(exit_code=code,audit_exit_code=monitor_code);save();print(json.dumps(state),flush=True)

if __name__=='__main__':main()
