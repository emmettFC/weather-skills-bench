"""Durable worker heartbeat; static exports never infer liveness from unfinished work."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time
from .catalog import ROOT


def output_stem(config):
    default='e2e' if config.get('study_role')=='end-to-end' else 'small-model' if config.get('study_role')=='small-model-extension' else 'expanded'
    stem=config.get('output_stem',default)
    if not isinstance(stem,str) or not stem or not stem.replace('-','').isalnum():
        raise ValueError('Study output stem must contain letters, numbers or hyphens')
    return stem


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


@contextmanager
def heartbeat(study_id):
    path = ROOT / 'results/health' / f'{study_id}.json'
    state = {'pid': os.getpid(), 'state': 'running', 'active': None}
    stop = threading.Event()
    lock = threading.Lock()
    def save():
        with lock:
            atomic_json(path, {**state, 'updated_at': datetime.now(timezone.utc).isoformat()})
    def loop():
        while not stop.wait(5):
            save()
    def update(**values):
        with lock:
            state.update(values)
        save()
    save()
    worker = threading.Thread(target=loop, daemon=True)
    worker.start()
    try:
        yield update
    except BaseException:
        update(state='stopped')
        raise
    else:
        update(state='finished', active=None)
    finally:
        stop.set()
        worker.join(timeout=6)


def study_health(study, now=None):
    if study.get('finished_at'):
        return {'state': 'complete' if len(study['runs']) == study['planned_runs'] else 'partial', 'updated_at': study['finished_at']}
    path = ROOT / 'results/health' / f"{study['study_id']}.json"
    try:
        data = json.loads(path.read_text())
        age = (now or time.time()) - datetime.fromisoformat(data['updated_at']).timestamp()
        os.kill(data['pid'], 0)
        live = data['state'] == 'running' and age <= 30
        return {'state': 'running' if live else 'stopped', 'updated_at': data['updated_at'], 'active': data.get('active') if live else None}
    except (OSError, ValueError, KeyError):
        return {'state': 'stopped', 'updated_at': None, 'active': None}
