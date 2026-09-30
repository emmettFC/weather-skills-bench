"""Archive the ECMWF S2S ensemble fields the forecast-skill oracle reads.

Only leads 1 to 14 days, which is what the case verifies. Written from the
catalogued c3s/ecmwf-s2s product, so the frozen bytes are the same fields an
agent retrieves rather than a re-export.
"""
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
INIT='2023-09-25'; KELVIN=273.15
sys.path.insert(0,'/Users/emmettculhane/Desktop/ACCORD/experiments/IOD-forecasting')


def freeze():
    import acmaddl, iod_pipeline as iod
    field=acmaddl.fetch(product='c3s/ecmwf-s2s',variable='sst',init=INIT,region=iod.REGION,verbose=False)['sst']-KELVIN
    day=(field['lead_time'].values/24).astype(int)
    field=field.isel(lead_time=np.flatnonzero((day>=1)&(day<=14)))
    build=ROOT/'.build/obs-raw';build.mkdir(parents=True,exist_ok=True)
    path=build/'s2s-iod.nc'
    field.to_dataset(name='sst').to_netcdf(path,encoding={'sst':{'zlib':True,'complevel':5}})
    blob=path.read_bytes()
    archive=ROOT/'fixtures/real-source-s2s-iod.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:z.writestr('s2s-iod.nc',blob)
    manifest=json.loads((ROOT/'fixtures/obs-sources.json').read_text())
    manifest['s2s-iod']={'url':'https://ecds.ecmwf.int/api c3s/ecmwf-s2s sst','init':INIT,'units':'degree_Celsius',
      'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'member':'s2s-iod.nc','member_sha256':hashlib.sha256(blob).hexdigest(),
      'bytes':len(blob),'dimensions':dict(field.sizes),
      'note':'Credentialed source. The sandbox holds no ECDS key and does not allowlist ecmwf.int, so this case runs outside the container until that is resolved.'}
    (ROOT/'fixtures/obs-sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f"froze {dict(field.sizes)}, {len(blob)/1e6:.2f} MB -> {archive.name}")


if __name__=='__main__':freeze()
