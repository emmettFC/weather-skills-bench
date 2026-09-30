"""Archive the ECMWF S2S ensemble fields the forecast-skill oracle reads.

Only leads 1 to 14 days, which is what the case verifies. Written from the
catalogued c3s/ecmwf-s2s product, so the frozen bytes are the same fields an
agent retrieves rather than a re-export. The control member needs an explicit
forecast_type; see freeze() and acmadDL PR #17.
"""
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
INIT='2023-09-25'; KELVIN=273.15
sys.path.insert(0,'/Users/emmettculhane/Desktop/ACCORD/experiments/IOD-forecasting')


def freeze():
    """Assemble the full 101-member ensemble: control as member 0, perturbed 1..100.

    Both halves come from the catalogued product, so the frozen bytes are the
    fields an agent retrieves rather than a re-export. The control needs an
    explicit forecast_type because the catalog pins the perturbed ensemble,
    which excludes it — a default fetch alone would average 100 of 101 members.
    """
    import acmaddl, iod_pipeline as iod
    def pull(**kw):
        return acmaddl.fetch(product='c3s/ecmwf-s2s',variable='sst',init=INIT,
                             region=iod.REGION,verbose=False,**kw)['sst']-KELVIN
    field=pull()
    ctrl=pull(forecast_type='control_forecast').expand_dims('member')
    assert np.array_equal(field['lead_time'].values,ctrl['lead_time'].values),'lead axes differ'
    field=xr.concat([ctrl,field],dim='member',coords='minimal',compat='override').sortby('member')
    assert field.sizes['member']==101, field.sizes
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
      'members':'control (0) plus 100 perturbed','note':'Credentialed source. The sandbox holds no ECDS key and does not allowlist ecmwf.int, so this case runs outside the container until that is resolved.'}
    (ROOT/'fixtures/obs-sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f"froze {dict(field.sizes)}, {len(blob)/1e6:.2f} MB -> {archive.name}")


if __name__=='__main__':freeze()
