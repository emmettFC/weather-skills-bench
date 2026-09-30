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


def control():
    """The control member, requested straight from ECDS.

    The catalogued product pins forecast_type to perturbed_forecast, so the
    library route returns the 100 perturbed members and no control. The task
    asks for the control and every perturbed member, matching the rest of the
    suite, so the oracle fetches the control itself. Requested as 24 hour
    periods because the plain hour list silently returns a single step.
    """
    import cdsapi, os, configparser
    rc=Path.home()/'.cdsapirc'
    conf=dict(line.split(':',1) for line in rc.read_text().splitlines() if ':' in line)
    client=cdsapi.Client(url=conf['url'].strip(),key=conf['key'].strip())
    target=ROOT/'.build/obs-raw/s2s-control.nc';target.parent.mkdir(parents=True,exist_ok=True)
    client.retrieve('s2s-forecasts',{'origin':'ecmwf','forecast_type':'control_forecast',
      'level_type':'single_level','variable':['sea_surface_temperature'],
      'year':'2023','month':'09','day':'25','time':'00:00',
      'leadtime_hour':[f'{24*d}_{24*(d+1)}' for d in range(0,14)],
      'area':[15,45,-15,115],'data_format':'netcdf'},str(target))
    ds=xr.open_dataset(target,decode_timedelta=False)['sst']-KELVIN
    ds=ds.rename({'latitude':'lat','longitude':'lon'})
    # Drop the scalar stamps that differ between the two requests; the lead
    # axis is reindexed onto the perturbed set's coordinate below.
    return ds.drop_vars([v for v in ('time','valid_time','surface','number') if v in ds.coords]).expand_dims(member=[0])


def freeze():
    import acmaddl, iod_pipeline as iod
    field=acmaddl.fetch(product='c3s/ecmwf-s2s',variable='sst',init=INIT,region=iod.REGION,verbose=False)['sst']-KELVIN
    day=(field['lead_time'].values/24).astype(int)
    field=field.isel(lead_time=np.flatnonzero((day>=1)&(day<=14)))
    ctrl=control().rename({'step':'lead_time'})
    ctrl=ctrl.assign_coords(lead_time=field['lead_time'].values)
    field=xr.concat([ctrl,field],dim='member',coords='minimal',compat='override').sortby('member')
    assert field.sizes['member']==101, field.sizes
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
