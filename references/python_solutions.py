"""Trusted one-program solutions. Never expose this file to an evaluated model.

Reads only /inputs and writes /work/answer.json using ordinary scientific Python.
CASE_ID is supplied by the reference validator, not a skill framework.
"""
import json
from pathlib import Path
import math
import numpy as np
import xarray as xr


def read(name):
    return xr.open_zarr('/inputs/'+name+'.zarr',chunks=None)


def strings(values):
    return [str(x)[:10] for x in values]


if CASE_ID=='rainfall-completeness':
    ds=read('rain').sel(latitude=slice(0,60),longitude=slice(30,31))
    times=ds.time.values.astype('datetime64[D]')
    weights=np.cos(np.radians(ds.latitude.values))
    values=[]; labels=[]
    for start in np.arange(np.datetime64('2024-01-01'),times.max()+1,np.timedelta64(7,'D')):
        mask=(times>=start)&(times<start+np.timedelta64(7,'D'))
        if mask.sum()!=7: continue
        total=ds.precip.values[mask].sum(axis=0)
        values.append(float(np.sum(total*weights[:,None])/(weights.sum()*len(ds.longitude))))
        labels.append(str(start))
    answer={'dates':labels,'totals_mm':values,'units':'mm'}
elif CASE_ID=='ensemble-flux-spread':
    ds=read('flux'); days=ds.step.values/np.timedelta64(1,'D')
    members=np.array([(ds.precip.values[:,(days>lo)&(days<=lo+7)]*86400).sum(axis=1) for lo in (0,7)])
    answer={'lead_days':[7,14],'spread_mm':np.std(members,axis=1,ddof=1).tolist(),'units':'mm'}
elif CASE_ID=='legacy-accumulation':
    ds=read('legacy'); increments=np.maximum(np.diff(ds.tp.values.squeeze(),axis=-1),0)
    days=ds.step.values[1:]/np.timedelta64(1,'D')
    med=[float(np.median(increments[:,(days>lo)&(days<=lo+7)].sum(axis=1))) for lo in (0,7)]
    answer={'lead_days':[7,14],'median_mm':med,'units':'mm'}
elif CASE_ID=='forecast-observation-bias':
    fc=read('forecast'); obs=read('obs')
    valid=(fc.time.values+fc.step.values).astype('datetime64[D]')
    ot=obs.time.values.astype('datetime64[D]')
    shared=np.intersect1d(valid,ot)
    fv=fc.t2m.transpose('step','latitude','longitude').values[:,0,:]-273.15
    ov=obs.temperature.transpose('time','latitude','longitude').values[:,0,:]
    errors=np.array([fv[np.flatnonzero(valid==t)[0]]-ov[np.flatnonzero(ot==t)[0]] for t in shared])
    answer={'dates':strings(shared),'errors_c':errors.tolist(),'bias_c':errors.mean(axis=0).tolist(),'units':'degree_Celsius'}
elif CASE_ID=='iod-anomaly':
    baseline=read('baseline'); target=read('target')
    anomaly=target.sst.values-baseline.sst.values.mean(axis=0)
    lat=target.latitude.values; lon=target.longitude.values
    def box(south,north,west,east):
        ilat=np.flatnonzero((lat>=south)&(lat<=north)); ilon=np.flatnonzero((lon>=west)&(lon<=east))
        field=anomaly[:,ilat][:,:,ilon]; w=np.cos(np.radians(lat[ilat]))
        return (np.sum(field*w[None,:,None],axis=(1,2))/(sum(w)*len(ilon))).tolist()
    west=box(-10,10,50,70); east=box(-10,0,90,110)
    answer={'dates':strings(target.time.values),'west_c':west,'east_c':east,'dmi_c':(np.array(west)-east).tolist(),'units':'degree_Celsius'}
elif CASE_ID=='multimodel-disagreement':
    values=[]
    for name in ('a','b','c'):
        ds=read(name); i=np.flatnonzero(ds.step.values==np.timedelta64(14,'D'))[0]
        values.append(ds.temperature.values[i]-(273.15 if ds.temperature.attrs['units']=='K' else 0))
    array=np.array(values)
    answer={'model_values_c':array.tolist(),'spread_c':np.std(array,axis=0,ddof=1).tolist(),'units':'degree_Celsius'}
elif CASE_ID=='rolling-nonoverlap':
    ds=read('rain'); values=[]
    for start in ('2024-01-01','2024-01-08'):
        t=np.datetime64(start); mask=(ds.time.values>=t)&(ds.time.values<t+np.timedelta64(7,'D'))
        assert mask.sum()==7
        values.append(float(ds.precip.values[mask].mean()*7))
    answer={'dates':['2024-01-01','2024-01-08'],'totals_mm':values,'units':'mm'}
elif CASE_ID=='calendar-alignment':
    model=read('model'); obs=read('obs')
    mt=strings(model.time.values); ot=strings(obs.time.values)
    shared=sorted(set(mt)&set(ot))
    error=[float(model.temperature.values[mt.index(t)]-273.15-obs.temperature.values[ot.index(t)]) for t in shared]
    answer={'dates':shared,'errors_c':error,'mean_bias_c':sum(error)/len(error),'units':'degree_Celsius'}
elif CASE_ID=='grid-alignment':
    from scipy.interpolate import RegularGridInterpolator
    fine=read('fine'); ref=read('ref')
    interp=RegularGridInterpolator((fine.latitude.values,fine.longitude.values),fine.temperature.values)
    x,y=np.meshgrid(ref.latitude.values,ref.longitude.values,indexing='ij')
    aligned=interp(np.column_stack([x.ravel(),y.ravel()])).reshape(x.shape)
    error=aligned-ref.temperature.values
    answer={'latitude':ref.latitude.values.tolist(),'longitude':ref.longitude.values.tolist(),'errors_c':error.tolist(),'mean_bias_c':float(error.mean()),'units':'degree_Celsius'}
elif CASE_ID=='duration-weighted-rainfall':
    ds=read('irregular'); bounds=ds.time_bounds.values
    values=[]
    for start in ('2024-01-01','2024-01-08'):
        left=np.datetime64(start); right=left+np.timedelta64(7,'D')
        days=np.maximum((np.minimum(bounds[:,1],right)-np.maximum(bounds[:,0],left))/np.timedelta64(1,'D'),0)
        assert days.sum()==7
        values.append(float(sum(ds.precip.values*days)))
    answer={'dates':['2024-01-01','2024-01-08'],'totals_mm':values,'units':'mm'}
else:
    raise ValueError(CASE_ID)

Path('/work/answer.json').write_text(json.dumps(answer,allow_nan=False))
