"""Archive the exact OISST fields the IOD oracle reads, with SHA256.

OISST arrives over OPeNDAP rather than an object store, so this freezes the
requested subset as one NetCDF instead of mirroring individual objects. 2023
fields are final; OISST revises for about two weeks after real time only.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
URL='https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc'
YEARS=list(range(2013,2024))                 # 2013-2022 climatology, 2023 target
DAYS=[(10,d) for d in range(1,8)]            # 1-7 October
BOX=dict(lat=slice(-10.5,10.5),lon=slice(49.5,110.5))   # union of both dipole boxes, with margin


def october_week(year):
    field=xr.open_dataset(URL.format(y=year))['sst'].sel(**BOX)
    stamps=pd.DatetimeIndex(field['time'].values)
    keep=np.flatnonzero([(m,d) in DAYS for m,d in zip(stamps.month,stamps.day)])
    return field.isel(time=keep).load()


def freeze():
    subset=xr.concat([october_week(y) for y in YEARS],dim='time').sortby('time')
    assert subset.sizes['time']==len(YEARS)*len(DAYS), subset.sizes
    build=ROOT/'.build/obs-raw';build.mkdir(parents=True,exist_ok=True)
    path=build/'oisst-iod.nc'
    subset.to_dataset(name='sst').to_netcdf(path,encoding={'sst':{'zlib':True,'complevel':5}})
    blob=path.read_bytes()
    archive=ROOT/'fixtures/real-source-oisst-iod.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        z.writestr('oisst-iod.nc',blob)
    manifest={'oisst-iod':{'url':URL,'years':YEARS,'days':[list(d) for d in DAYS],
        'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'member':'oisst-iod.nc','member_sha256':hashlib.sha256(blob).hexdigest(),
        'bytes':len(blob),'dimensions':dict(subset.sizes)}}
    (ROOT/'fixtures/obs-sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f"froze {subset.sizes['time']} daily fields, {subset.sizes['lat']}x{subset.sizes['lon']} grid, "
          f"{len(blob)/1e6:.2f} MB -> {archive.name}")
    return manifest


if __name__=='__main__':
    freeze()
