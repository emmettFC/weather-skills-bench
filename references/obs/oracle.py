"""Independent NumPy oracle for the observed dipole, from frozen raw OISST.

Reads the hash-checked archive, never a skill or library output. Weighted means
are formed with explicit NumPy sums so the answer does not inherit any
convenience wrapper's weighting or missing-value convention.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
WEST=dict(lat=(-10.0,10.0),lon=(50.0,70.0))
EAST=dict(lat=(-10.0,0.0),lon=(90.0,110.0))
TARGET='2023'


def restore():
    """Reconstruct the oracle input from versioned, hash-checked bytes."""
    manifest=json.loads((ROOT/'fixtures/obs-sources.json').read_text())['oisst-iod']
    archive=ROOT/'fixtures'/manifest['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('OISST archive hash mismatch')
    with zipfile.ZipFile(archive) as source:
        if source.namelist()!=[manifest['member']]:raise ValueError('Unexpected archive members')
        blob=source.read(manifest['member'])
    if hashlib.sha256(blob).hexdigest()!=manifest['member_sha256']:raise ValueError('OISST member hash mismatch')
    dest=ROOT/'.build/obs-raw';dest.mkdir(parents=True,exist_ok=True)
    path=dest/manifest['member'];path.write_bytes(blob)
    return path


def box_mean(values,lat,lon,box):
    """Cosine-latitude weighted mean over centres inside the closed interval,
    weights renormalised over the cells that carry a value."""
    iy=np.flatnonzero((lat>=box['lat'][0])&(lat<=box['lat'][1]))
    ix=np.flatnonzero((lon>=box['lon'][0])&(lon<=box['lon'][1]))
    sub=values[:,iy][:,:,ix]
    w=np.cos(np.deg2rad(lat[iy]))[None,:,None]*np.ones((1,1,ix.size))
    valid=np.isfinite(sub)
    return np.sum(np.where(valid,sub*w,0.0),axis=(1,2))/np.sum(np.where(valid,w,0.0),axis=(1,2))


def answers():
    ds=xr.open_dataset(restore())
    lat=ds['lat'].values;lon=ds['lon'].values
    stamps=pd.DatetimeIndex(ds['time'].values)
    sst=ds['sst'].values.astype('float64')
    target=stamps.year==int(TARGET)
    clim=np.nanmean(sst[~target],axis=0)                    # one field, ten years of 1-7 October
    anomaly=sst[target]-clim[None,:,:]
    west=box_mean(anomaly,lat,lon,WEST);east=box_mean(anomaly,lat,lon,EAST)
    order=np.argsort(stamps[target].values)
    return {'dates':[str(d.date()) for d in stamps[target][order]],
            'west_c':west[order].tolist(),'east_c':east[order].tolist(),
            'dmi_c':(west-east)[order].tolist(),'units':'degree_Celsius',
            'source_url':'https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.2023.nc'}


if __name__=='__main__':
    result=answers()
    (Path(__file__).parent/'answers.json').write_text(json.dumps({'iod-dmi-observed':result},indent=2)+'\n')
    print(f"{'date':12s} {'west_c':>10s} {'east_c':>10s} {'dmi_c':>10s}")
    for d,w,e,m in zip(result['dates'],result['west_c'],result['east_c'],result['dmi_c']):
        print(f'{d:12s} {w:10.6f} {e:10.6f} {m:10.6f}')
