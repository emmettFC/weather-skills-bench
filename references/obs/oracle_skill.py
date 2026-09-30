"""Independent NumPy oracle for the persistence-skill case, from frozen OISST.

Explicit weighted sums rather than a convenience wrapper, so agreement with the
one-program solution is a check rather than a restatement.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
WEST=dict(lat=(-10.0,10.0),lon=(50.0,70.0))
EAST=dict(lat=(-10.0,0.0),lon=(90.0,110.0))
EARLY,LATE='2023-09-24','2023-10-01'
VERIFY=pd.date_range('2023-10-02','2023-10-08')


def restore():
    entry=json.loads((ROOT/'fixtures/obs-sources.json').read_text())['oisst-iod-skill']
    archive=ROOT/'fixtures'/entry['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=entry['archive_sha256']:
        raise ValueError('OISST skill archive hash mismatch')
    with zipfile.ZipFile(archive) as src:blob=src.read(entry['member'])
    if hashlib.sha256(blob).hexdigest()!=entry['member_sha256']:raise ValueError('member hash mismatch')
    dest=ROOT/'.build/obs-raw';dest.mkdir(parents=True,exist_ok=True)
    path=dest/entry['member'];path.write_bytes(blob);return path


def box_mean(values,lat,lon,box):
    iy=np.flatnonzero((lat>=box['lat'][0])&(lat<=box['lat'][1]))
    ix=np.flatnonzero((lon>=box['lon'][0])&(lon<=box['lon'][1]))
    sub=values[:,iy][:,:,ix]
    w=np.cos(np.deg2rad(lat[iy]))[None,:,None]*np.ones((1,1,ix.size))
    ok=np.isfinite(sub)
    return np.sum(np.where(ok,sub*w,0.0),axis=(1,2))/np.sum(np.where(ok,w,0.0),axis=(1,2))


def answers():
    ds=xr.open_dataset(restore())
    lat,lon=ds['lat'].values,ds['lon'].values
    stamps=pd.DatetimeIndex(ds['time'].values);sst=ds['sst'].values.astype('float64')
    target=stamps.year==2023
    clim=np.nanmean(sst[~target],axis=0)
    anomaly=sst[target]-clim[None,:,:];days=stamps[target]
    dmi=box_mean(anomaly,lat,lon,WEST)-box_mean(anomaly,lat,lon,EAST)
    at=lambda d:float(dmi[np.flatnonzero(days==pd.Timestamp(d))[0]])
    idx=[np.flatnonzero(days==d)[0] for d in VERIFY]
    observed=dmi[idx];early,late=at(EARLY),at(LATE)
    err_early=(early-observed);err_late=(late-observed)
    return {'dates':[str(d.date()) for d in VERIFY],'observed_dmi_c':observed.tolist(),
            'forecast_early_c':early,'forecast_late_c':late,
            'error_early_c':err_early.tolist(),'error_late_c':err_late.tolist(),
            'bias_early_c':float(err_early.mean()),'bias_late_c':float(err_late.mean()),
            'units':'degree_Celsius','figure':'/work/outlook.png',
            'source_url':'https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.2023.nc'}


if __name__=='__main__':
    r=answers()
    path=Path(__file__).parent/'answers.json'
    existing=json.loads(path.read_text()) if path.exists() else {}
    existing['iod-persistence-skill']=r
    path.write_text(json.dumps(existing,indent=2)+'\n')
    print(f"forecast early {r['forecast_early_c']:+.6f}  late {r['forecast_late_c']:+.6f}")
    print(f"bias     early {r['bias_early_c']:+.6f}  late {r['bias_late_c']:+.6f}")
