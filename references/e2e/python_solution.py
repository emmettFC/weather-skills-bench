"""Trusted Python-only feasibility solution; never mounted for evaluated agents."""
import json
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
BASE='https://storage.googleapis.com/kenya-forecasting-data/'

def source(date,product):
    return BASE+date+'/data/ECMWF_s2s_'+product+'_'+date+'.zarr'

def read(date,product,var):
    ds=xr.open_zarr(source(date,product),chunks=None,consolidated=True)
    ilat=np.flatnonzero((ds.latitude.values>=-5)&(ds.latitude.values<=5))
    ilon=np.flatnonzero((ds.longitude.values>=34)&(ds.longitude.values<=42))
    ds=ds.isel(latitude=ilat,longitude=ilon)
    return ds[var].transpose('number','step','latitude','longitude').values.astype(float),ds.latitude.values,ds.longitude.values

def regional(a,lat):
    return np.average(a.mean(axis=-1),axis=-1,weights=np.cos(np.radians(lat)))

def weeks(date):
    a,lat,lon=read(date,'precip','tp')
    daily=np.maximum(a[:,1:]-a[:,:-1],0)
    return daily[:,:42].reshape(101,6,7,len(lat),len(lon)).sum(axis=2),lat,lon

if CASE_ID=='e2e-kenya-heat':
    a,lat,lon=read('2026-09-27','daily_vars','t2m')
    peak=regional(a[:,:14]-273.15,lat).reshape(101,2,7).max(axis=-1)
    answer={'period_end_lead_days':[7,14],'median_peak_c':np.median(peak,axis=0).tolist(),'peak_spread_c':np.std(peak,axis=0,ddof=1).tolist(),
        'minimum_member_peak_c':peak.min(axis=0).tolist(),'maximum_member_peak_c':peak.max(axis=0).tolist(),'units':'degree_Celsius','source_url':source('2026-09-27','daily_vars'),'figure':'/work/outlook.png'}
    fig,ax=plt.subplots(figsize=(9,5));ax.plot(['2026-10-04','2026-10-11'],answer['median_peak_c'],marker='o');ax.set_ylabel('Median hottest daily regional mean (°C)');ax.set_xlabel('Forecast period end');ax.set_title('ECMWF S2S Kenya heat outlook · issue 2026-09-27');ax.grid(alpha=.3)
else:
    a,lat,lon=weeks('2026-09-27')
    answer={'latitude':lat.tolist(),'longitude':lon.tolist(),'units':'mm','figure':'/work/outlook.png'}
    if CASE_ID=='e2e-kenya-rainfall':
        reg=regional(a,lat);maps=a.mean(axis=0)
        answer.update(period_end_lead_days=[7,14,21,28,35,42],ensemble_mean_mm=maps.tolist(),regional_median_mm=np.median(reg,axis=0).tolist(),regional_spread_mm=np.std(reg,axis=0,ddof=1).tolist(),source_url=source('2026-09-27','precip'))
        titles=['Week '+str(i+1)+' · lead '+str(7*(i+1))+'d' for i in range(6)];cmap='Blues';title='ECMWF S2S ensemble mean rainfall · issue 2026-09-27'
    elif CASE_ID=='e2e-kenya-revision':
        b,_,_=weeks('2026-09-20');current=a[:,:2].mean(axis=0);previous=b[:,1:3].mean(axis=0);maps=current-previous
        answer.update(valid_period_end_dates=['2026-10-04','2026-10-11'],current_mean_mm=current.tolist(),previous_mean_mm=previous.tolist(),change_mm=maps.tolist(),regional_change_mm=regional(maps,lat).tolist(),current_source_url=source('2026-09-27','precip'),previous_source_url=source('2026-09-20','precip'))
        titles=['Period ending 2026-10-04','Period ending 2026-10-11'];cmap='RdBu';title='Rainfall outlook change · Sep 27 minus Sep 20 issue'
    else:raise ValueError(CASE_ID)
    fig,axes=plt.subplots(1,len(maps),figsize=(4*len(maps),5),squeeze=False,layout='constrained')
    for ax,field,label in zip(axes[0],maps,titles):
        im=ax.pcolormesh(lon,lat,field,cmap=cmap,vmin=float(maps.min()),vmax=float(maps.max()));ax.set_title(label);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    fig.colorbar(im,ax=list(axes[0]),label='Rainfall (mm)');fig.suptitle(title)
fig.savefig('/work/outlook.png',dpi=100)
Path('/work/answer.json').write_text(json.dumps(answer,allow_nan=False))
