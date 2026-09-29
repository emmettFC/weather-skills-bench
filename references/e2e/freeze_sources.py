"""Archive exact public source objects, retaining GCS generations and SHA256."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
BUCKET='kenya-forecasting-data'
SOURCES={
 'rain-current':'2026-09-27/data/ECMWF_s2s_precip_2026-09-27.zarr',
 'rain-previous':'2026-09-20/data/ECMWF_s2s_precip_2026-09-20.zarr',
 'temperature':'2026-09-27/data/ECMWF_s2s_daily_vars_2026-09-27.zarr',
}

def fetch_source(item):
 name,prefix=item;dest=ROOT/'.build/e2e-raw'/name;dest.mkdir(parents=True,exist_ok=True)
 token=None;objects=[]
 while True:
  params={'prefix':prefix+'/','maxResults':1000}
  if token:params['pageToken']=token
  url=f'https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?'+urllib.parse.urlencode(params)
  listing=json.load(urllib.request.urlopen(url,timeout=60));objects.extend(listing.get('items',[]))
  token=listing.get('nextPageToken')
  if not token:break
 assert objects, prefix
 def download(obj):
  relative=obj['name'][len(prefix)+1:];path=dest/relative
  url=f"https://storage.googleapis.com/{BUCKET}/{obj['name']}?generation={obj['generation']}"
  blob=urllib.request.urlopen(url,timeout=60).read()
  assert len(blob)==int(obj['size'])
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
  return {'path':relative,'generation':obj['generation'],'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(download,objects))
 archive=ROOT/'fixtures'/f'real-source-{name}.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
  for entry in sorted(entries,key=lambda e:e['path']):
   info=zipfile.ZipInfo(entry['path'],date_time=(1980,1,1,0,0,0));info.external_attr=0o100644<<16
   z.writestr(info,(dest/entry['path']).read_bytes())
 print(name,len(entries),sum(x['bytes'] for x in entries),'bytes',flush=True)
 return name,{'url':f'https://storage.googleapis.com/{BUCKET}/{prefix}','objects':entries,'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'retrieved_at':datetime.now(timezone.utc).isoformat()}

if __name__=='__main__':
 result=dict(fetch_source(item) for item in SOURCES.items())
 (ROOT/'fixtures/real-sources.json').write_text(json.dumps(result,indent=2)+'\n')
