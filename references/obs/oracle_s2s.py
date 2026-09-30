"""Independent NumPy oracle for the S2S forecast-skill case, from frozen bytes.

Model and observations sit on different grids, so each box mean is taken on its
own grid rather than regridding one onto the other. The observed climatology is
used on both sides, so it cancels in the error while still setting the level of
the reported anomalies.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT=Path(__file__).resolve().parents[2]
INIT='2023-09-25'
WEST=dict(lat=(-10.,10.),lon=(50.,70.));EAST=dict(lat=(-10.,0.),lon=(90.,110.))
WINDOWS={'d1_7':(1,7),'d8_14':(8,14)}


def restore(key):
    entry=json.loads((ROOT/'fixtures/obs-sources.json').read_text())[key]
    archive=ROOT/'fixtures'/entry['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=entry['archive_sha256']:
        raise ValueError(f'Archive hash mismatch: {key}')
    with zipfile.ZipFile(archive) as src:blob=src.read(entry['member'])
    if hashlib.sha256(blob).hexdigest()!=entry['member_sha256']:raise ValueError(f'Member hash mismatch: {key}')
    dest=ROOT/'.build/obs-raw';dest.mkdir(parents=True,exist_ok=True)
    path=dest/entry['member'];path.write_bytes(blob);return path


def box(values,lat,lon,b):
    """Cosine-latitude weighted mean over centres in the closed interval,
    weights renormalised over the cells that carry a value."""
    iy=np.flatnonzero((lat>=b['lat'][0])&(lat<=b['lat'][1]))
    ix=np.flatnonzero((lon>=b['lon'][0])&(lon<=b['lon'][1]))
    sub=values[...,iy,:][...,:,ix]
    w=np.cos(np.deg2rad(lat[iy]))[:,None]*np.ones((1,ix.size))
    ok=np.isfinite(sub)
    return np.sum(np.where(ok,sub*w,0.0),axis=(-2,-1))/np.sum(np.where(ok,w,0.0),axis=(-2,-1))


def answers():
    m=xr.open_dataset(restore('s2s-iod'),decode_timedelta=False)['sst']
    o=xr.open_dataset(restore('oisst-iod-skill'))['sst']
    mlat,mlon=m['lat'].values,m['lon'].values;olat,olon=o['lat'].values,o['lon'].values
    stamps=pd.DatetimeIndex(o['time'].values);is23=stamps.year==2023
    clim=o.values[~is23].mean(axis=0)
    cw=float(box(clim,olat,olon,WEST));ce=float(box(clim,olat,olon,EAST))
    obs=o.values[is23];odays=stamps[is23]
    day=(m['lead_time'].values/24).astype(int)
    result={'valid_from':[],'valid_to':[],
            'forecast_dmi_c':[],'spread_dmi_c':[],'observed_dmi_c':[],'error_dmi_c':[]}
    for name,(a,b) in WINDOWS.items():
        sub=m.values[:,np.flatnonzero((day>=a)&(day<=b))].mean(axis=1)      # (member, lat, lon)
        member_dmi=(box(sub,mlat,mlon,WEST)-cw)-(box(sub,mlat,mlon,EAST)-ce)
        days=pd.date_range(INIT,periods=14)[a-1:b]
        sel=np.flatnonzero(np.isin(odays,days))
        ow=float(box(obs[sel].mean(axis=0),olat,olon,WEST));oe=float(box(obs[sel].mean(axis=0),olat,olon,EAST))
        observed=(ow-cw)-(oe-ce)
        result['valid_from'].append(str(days[0].date()));result['valid_to'].append(str(days[-1].date()))
        result['forecast_dmi_c'].append(float(member_dmi.mean()))
        result['spread_dmi_c'].append(float(member_dmi.std(ddof=1)))
        result['observed_dmi_c'].append(observed)
        result['error_dmi_c'].append(float(member_dmi.mean())-observed)
    result.update(units='degree_Celsius',figure='/work/outlook.png',
                  source_url='https://ecds.ecmwf.int/api c3s/ecmwf-s2s sst init 2023-09-25')
    return result


if __name__=='__main__':
    r=answers();path=Path(__file__).parent/'answers.json'
    existing=json.loads(path.read_text()) if path.exists() else {}
    existing['iod-s2s-forecast-skill']=r
    path.write_text(json.dumps(existing,indent=2)+'\n')
    for i in range(len(r['valid_from'])):
        print(f"{r['valid_from'][i]} to {r['valid_to'][i]}  forecast {r['forecast_dmi_c'][i]:+.6f}  "
              f"spread {r['spread_dmi_c'][i]:.6f}  observed {r['observed_dmi_c'][i]:+.6f}  error {r['error_dmi_c'][i]:+.6f}")
