"""Archive the OISST fields the S2S forecast-skill oracle reads, with SHA256.

A wider window than the index case: 24 September to 8 October, so one frozen
climatology covers both forecast periods and the days they verify against.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
URL='https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc'
YEARS=list(range(2013,2024))
BOX=dict(lat=slice(-10.5,10.5),lon=slice(49.5,110.5))


def window(year):
    field=xr.open_dataset(URL.format(y=year))['sst'].sel(**BOX)
    stamps=pd.DatetimeIndex(field['time'].values)
    keep=((stamps.month==9)&(stamps.day>=24))|((stamps.month==10)&(stamps.day<=8))
    return field.isel(time=np.flatnonzero(keep)).load()


def freeze():
    subset=xr.concat([window(y) for y in YEARS],dim='time').sortby('time')
    assert subset.sizes['time']==len(YEARS)*15, subset.sizes
    build=ROOT/'.build/obs-raw';build.mkdir(parents=True,exist_ok=True)
    path=build/'oisst-iod-skill.nc'
    subset.to_dataset(name='sst').to_netcdf(path,encoding={'sst':{'zlib':True,'complevel':5}})
    blob=path.read_bytes()
    archive=ROOT/'fixtures/real-source-oisst-iod-skill.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:z.writestr('oisst-iod-skill.nc',blob)
    manifest=json.loads((ROOT/'fixtures/obs-sources.json').read_text())
    manifest['oisst-iod-skill']={'url':URL,'years':YEARS,'window':'24 September to 8 October',
        'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'member':'oisst-iod-skill.nc','member_sha256':hashlib.sha256(blob).hexdigest(),
        'bytes':len(blob),'dimensions':dict(subset.sizes)}
    (ROOT/'fixtures/obs-sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f"froze {subset.sizes['time']} daily fields, {len(blob)/1e6:.2f} MB -> {archive.name}")


if __name__=='__main__':freeze()
