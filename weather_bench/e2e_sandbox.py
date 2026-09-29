"""Fresh agent containers with source-only HTTP access; no model API credentials."""
import json
from pathlib import Path
import shutil
import subprocess
import uuid
from .catalog import ROOT,DEFAULT_CATALOG,CORE_COMMIT,inventory,verify
from .sandbox import Sandbox,ENABLED

E2E_ENABLED=ENABLED|{'kenya-forecast-fetch','resolve-region','resolve-time','plot'}


def build_images():
    verify();context=ROOT/'.build/docker-e2e';context.mkdir(parents=True,exist_ok=True)
    shutil.copy(ROOT/'requirements-e2e.lock',context/'requirements.txt')
    shutil.copy(ROOT/'weather_bench/source_proxy.py',context/'source_proxy.py')
    shutil.copy(ROOT/'docker/e2e/sitecustomize.py',context/'sitecustomize.py')
    (context/'Dockerfile').write_text('''FROM weather-bench-python:v1 AS python
COPY requirements.txt /tmp/e2e-requirements.txt
RUN pip install --no-cache-dir -r /tmp/e2e-requirements.txt
RUN python -c "import cartopy; from cartopy.io import shapereader; cartopy.config['data_dir']='/opt/cartopy'; [shapereader.natural_earth(resolution=r,category=c,name=n) for r in ('10m','50m','110m') for c,n in [('physical','coastline'),('cultural','admin_0_boundary_lines_land')]]"
COPY sitecustomize.py /runtime/sitecustomize.py
COPY source_proxy.py /runtime/source_proxy.py
ENV MPLCONFIGDIR=/tmp/matplotlib MPLBACKEND=Agg CARTOPY_DATA_DIR=/opt/cartopy
FROM python AS skills
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --no-deps "weather-skills-core @ git+https://github.com/rhiza-research/weather-skills-core@'''+CORE_COMMIT+'''"
COPY catalog /catalog
''')
    for name,entry in inventory().items():
        if name in E2E_ENABLED:
            folder=Path(entry['doc']).parent
            target=context/'catalog'/folder
            if target.exists():shutil.rmtree(target)
            shutil.copytree(DEFAULT_CATALOG/folder,target,ignore=shutil.ignore_patterns('tests','__pycache__'))
    for target in ('python','skills'):
        subprocess.run(['docker','build','--target',target,'-t',f'weather-bench-{target}:e2e-v1',str(context)],check=True)


class E2ESandbox(Sandbox):
    def __init__(self,*args,**kwargs):
        self.network='weather-source-'+uuid.uuid4().hex
        self.proxy='weather-proxy-'+uuid.uuid4().hex
        self.network_events=[];self.containers={}
        try:
            subprocess.run(['docker','network','create','--internal',self.network],capture_output=True,check=True)
            subprocess.run(['docker','run','-d','--name',self.proxy,'--read-only','--cap-drop=ALL','--security-opt','no-new-privileges','--memory','128m','--user','65534:65534','weather-bench-python:e2e-v1','python','/runtime/source_proxy.py'],capture_output=True,check=True)
            subprocess.run(['docker','network','connect','--alias','source-proxy',self.network,self.proxy],capture_output=True,check=True)
            super().__init__(*args,**kwargs,runtime={'network':self.network,'tag':'e2e-v1','enabled':E2E_ENABLED,
                'environment':{'HTTPS_PROXY':'http://source-proxy:8080','HTTP_PROXY':'http://source-proxy:8080','PYTHONPATH':'/runtime'},'memory':'2g'})
        except BaseException:
            self.close();raise

    def close(self):
        super().close()
        if getattr(self,'proxy',None):
            logs=subprocess.run(['docker','logs',self.proxy],capture_output=True,text=True).stdout
            for line in logs.splitlines():
                try:self.network_events.append(json.loads(line))
                except ValueError:pass
            subprocess.run(['docker','rm','-f',self.proxy],capture_output=True,timeout=30);self.proxy=None
        if getattr(self,'network',None):
            subprocess.run(['docker','network','rm',self.network],capture_output=True,timeout=30);self.network=None
