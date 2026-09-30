"""Independent NumPy oracle from raw provider archives, never fetcher outputs."""
import json
import hashlib
import zipfile
from pathlib import Path
import numpy as np
import xarray as xr
ROOT=Path(__file__).resolve().parents[2]


def restore_sources():
    """Reconstruct the private oracle inputs from versioned, hash-checked bytes."""
    manifest=json.loads((ROOT/'fixtures/real-sources.json').read_text())
    for name,entry in manifest.items():
        archive=ROOT/'fixtures'/entry['archive']
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=entry['archive_sha256']:
            raise ValueError('Raw archive hash mismatch: '+name)
        dest=ROOT/'.build/e2e-raw'/name
        with zipfile.ZipFile(archive) as source:
            expected={obj['path']:obj for obj in entry['objects']}
            if set(source.namelist())!=set(expected):raise ValueError('Unexpected source archive members')
            for path,obj in expected.items():
                relative=Path(path)
                if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe source archive path')
                blob=source.read(path)
                if hashlib.sha256(blob).hexdigest()!=obj['sha256']:raise ValueError('Source object hash mismatch')
                target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)


def raw(name,var):
    ds=xr.open_zarr(ROOT/'.build/e2e-raw'/name,chunks=None)
    lat=ds.latitude.values;lon=ds.longitude.values
    iy=np.flatnonzero((lat>=-5)&(lat<=5));ix=np.flatnonzero((lon>=34)&(lon<=42))
    return ds,ds[var].transpose('number','step','latitude','longitude').values[:,:,iy][:,:,:,ix],lat[iy],lon[ix]


def area(a,lat):
    w=np.cos(np.deg2rad(lat))
    return np.sum(a*w[None,None,:,None],axis=(-2,-1))/(sum(w)*a.shape[-1])


def weekly(name):
    ds,a,lat,lon=raw(name,'tp')
    assert ds.tp.attrs['units']=='kg m**-2'
    inc=np.maximum(np.diff(a.astype('float64'),axis=1),0) # 1 kg m-2 liquid water = 1 mm
    lead=(ds.step.values[1:]/np.timedelta64(1,'D')).astype(int)
    values=np.stack([inc[:,(lead>lo)&(lead<=lo+7)].sum(axis=1) for lo in range(0,42,7)],axis=1)
    assert values.shape[1]==6 and all(np.count_nonzero((lead>lo)&(lead<=lo+7))==7 for lo in range(0,42,7))
    return values,lat,lon


def calculate():
    a,lat,lon=weekly('rain-current');r=area(a,lat)
    base='https://storage.googleapis.com/kenya-forecasting-data/'
    current=base+'2026-09-27/data/ECMWF_s2s_precip_2026-09-27.zarr'
    previous=base+'2026-09-20/data/ECMWF_s2s_precip_2026-09-20.zarr'
    common={'latitude':lat.tolist(),'longitude':lon.tolist(),'figure':'/work/outlook.png'}
    rain={**common,'period_end_lead_days':[7,14,21,28,35,42],'ensemble_mean_mm':a.mean(axis=0).tolist(),
          'regional_median_mm':np.median(r,axis=0).tolist(),'regional_spread_mm':r.std(axis=0,ddof=1).tolist(),'units':'mm','source_url':current}
    b,_,_=weekly('rain-previous');new=a[:,:2].mean(axis=0);old=b[:,1:3].mean(axis=0);delta=new-old
    change={**common,'valid_period_end_dates':['2026-10-04','2026-10-11'],'current_mean_mm':new.tolist(),'previous_mean_mm':old.tolist(),
            'change_mm':delta.tolist(),'regional_change_mm':area(delta[None],lat)[0].tolist(),'units':'mm','current_source_url':current,'previous_source_url':previous}
    ds,t,lat,lon=raw('temperature','t2m');assert ds.t2m.attrs['units']=='K'
    t=t.astype('float64')-273.15
    # Hottest forecast daily regional mean in each week, then summarize members.
    regional=area(t,lat);peaks=np.stack([regional[:,lo:lo+7].max(axis=1) for lo in (0,7)],axis=1)
    heat={'period_end_lead_days':[7,14],'median_peak_c':np.median(peaks,axis=0).tolist(),'peak_spread_c':peaks.std(axis=0,ddof=1).tolist(),
          'minimum_member_peak_c':peaks.min(axis=0).tolist(),'maximum_member_peak_c':peaks.max(axis=0).tolist(),'units':'degree_Celsius',
          'source_url':base+'2026-09-27/data/ECMWF_s2s_daily_vars_2026-09-27.zarr','figure':'/work/outlook.png'}
    return {'e2e-kenya-rainfall':rain,'e2e-kenya-revision':change,'e2e-kenya-heat':heat,**dipole()}


def dipole():
    """The Indian Ocean Dipole answers, from the oracles that own them.

    They live in references/obs because their sources are NOAA PSL and the
    ECMWF Data Stores rather than the Kenya object archive, and each restores
    and hash-checks its own frozen bytes. Delegating keeps one oracle per set
    of ground truth while still presenting every end-to-end answer here.
    """
    import importlib.util
    out={}
    for module,case in (('oracle','iod-dmi-observed-skill'),
                        ('oracle_s2s','iod-s2s-forecast-skill')):
        spec=importlib.util.spec_from_file_location(f'obs_{module}',ROOT/'references/obs'/f'{module}.py')
        loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded)
        out[case]=loaded.answers()
    return out

if __name__=='__main__':
    restore_sources()
    (ROOT/'references/e2e/answers.json').write_text(json.dumps(calculate(),indent=2,allow_nan=False)+'\n')
