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

if CASE_ID=='iod-persistence-skill':
    import pandas as pd
    OISST='https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc'
    def window(y):
        f=xr.open_dataset(OISST.format(y=y))['sst'].sel(lat=slice(-10.5,10.5),lon=slice(49.5,110.5))
        t=pd.DatetimeIndex(f['time'].values)
        return f.isel(time=np.flatnonzero(((t.month==9)&(t.day>=24))|((t.month==10)&(t.day<=8)))).load()
    def box(a,la0,la1,lo0,lo1):
        s=a.sel(lat=slice(la0,la1),lon=slice(lo0,lo1))
        return s.weighted(np.cos(np.radians(s['lat']))).mean(('lat','lon'))
    clim=xr.concat([window(y) for y in range(2013,2023)],dim='time').mean('time')
    anom=window(2023).sortby('time')-clim
    dmi=box(anom,-10,10,50,70)-box(anom,-10,0,90,110)
    verify=pd.date_range('2023-10-02','2023-10-08')
    obs=dmi.sel(time=verify).values
    early=float(dmi.sel(time='2023-09-24').values);late=float(dmi.sel(time='2023-10-01').values)
    ee=(early-obs);el=(late-obs)
    days=[str(d.date()) for d in verify]
    answer={'dates':days,'observed_dmi_c':obs.tolist(),'forecast_early_c':early,'forecast_late_c':late,
            'error_early_c':ee.tolist(),'error_late_c':el.tolist(),
            'bias_early_c':float(ee.mean()),'bias_late_c':float(el.mean()),
            'units':'degree_Celsius','source_url':OISST.format(y=2023),'figure':'/work/outlook.png'}
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.plot(days,obs,marker='o',label='Observed dipole index')
    ax.plot(days,ee,marker='s',label='Error, issued 24 Sep')
    ax.plot(days,el,marker='^',label='Error, issued 1 Oct')
    ax.axhline(0,color='#444',lw=.8);ax.set_ylabel('degree_Celsius')
    ax.set_title('Dipole persistence forecasts against observations, 2-8 October 2023')
    ax.legend(frameon=False);ax.tick_params(axis='x',rotation=45);fig.tight_layout()
    fig.savefig('/work/outlook.png',dpi=120)
elif CASE_ID=='iod-dmi-observed':
    import pandas as pd
    OISST='https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc'
    OCT=[(10,d) for d in range(1,8)]
    def october(year):
        f=xr.open_dataset(OISST.format(y=year))['sst'].sel(lat=slice(-10.5,10.5),lon=slice(49.5,110.5))
        t=pd.DatetimeIndex(f['time'].values)
        return f.isel(time=np.flatnonzero([(m,d) in OCT for m,d in zip(t.month,t.day)])).load()
    def box(anom,lat0,lat1,lon0,lon1):
        sub=anom.sel(lat=slice(lat0,lat1),lon=slice(lon0,lon1))
        return sub.weighted(np.cos(np.radians(sub['lat']))).mean(('lat','lon'))
    clim=xr.concat([october(y) for y in range(2013,2023)],dim='time').mean('time')
    target=october(2023).sortby('time');anom=target-clim
    west=box(anom,-10,10,50,70);east=box(anom,-10,0,90,110);dmi=west-east
    days=[str(pd.Timestamp(t).date()) for t in target['time'].values]
    answer={'dates':days,'west_c':[float(x) for x in west.values],'east_c':[float(x) for x in east.values],
            'dmi_c':[float(x) for x in dmi.values],'units':'degree_Celsius',
            'source_url':OISST.format(y=2023),'figure':'/work/outlook.png'}
    fig,ax=plt.subplots(figsize=(8,4.5))
    for series,label in ((west,'West 50-70E, 10S-10N'),(east,'East 90-110E, 10S-0'),(dmi,'Dipole index')):
        ax.plot(days,series.values,marker='o',label=label)
    ax.axhline(0,color='#444',lw=.8);ax.set_ylabel('SST anomaly (degree_Celsius)')
    ax.set_title('Observed Indian Ocean Dipole, 1-7 October 2023')
    ax.legend(frameon=False);ax.tick_params(axis='x',rotation=45);fig.tight_layout()
    fig.savefig('/work/outlook.png',dpi=120)
elif CASE_ID=='e2e-kenya-heat':
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
