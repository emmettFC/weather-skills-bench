"""Reference solution for iod-dmi-observed-skill, the code arm.

One program, public sources only, no skills and no ACCORD libraries. Mirrors
what a competent agent should write. The oracle in oracle.py is deliberately a
different implementation reading frozen bytes, so agreement between them is a
real check rather than a restatement.
"""
import json
import numpy as np, pandas as pd, xarray as xr

URL='https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{y}.nc'
DAYS=[(10,d) for d in range(1,8)]          # 1-7 October
CLIM_YEARS=range(2013,2023)
TARGET=2023
WEST=dict(lat=(-10.0,10.0),lon=(50.0,70.0))
EAST=dict(lat=(-10.0,0.0),lon=(90.0,110.0))


def october_week(year):
    """The seven 1-7 October fields for one year, over both dipole boxes."""
    field=xr.open_dataset(URL.format(y=year))['sst'].sel(lat=slice(-10.5,10.5),lon=slice(49.5,110.5))
    stamps=pd.DatetimeIndex(field['time'].values)
    return field.isel(time=np.flatnonzero([(m,d) in DAYS for m,d in zip(stamps.month,stamps.day)])).load()


def box_mean(anomaly,box):
    """Cosine-latitude weighted mean over the grid centres inside the closed
    interval. xarray's weighted mean skips missing cells and renormalises the
    weights over the rest, which is what the land in the eastern box requires."""
    sub=anomaly.sel(lat=slice(*box['lat']),lon=slice(*box['lon']))
    return sub.weighted(np.cos(np.deg2rad(sub['lat']))).mean(('lat','lon'))


def solve():
    climatology=xr.concat([october_week(y) for y in CLIM_YEARS],dim='time').mean('time')
    target=october_week(TARGET).sortby('time')
    anomaly=target-climatology                       # the field broadcasts across the seven days
    west=box_mean(anomaly,WEST);east=box_mean(anomaly,EAST)
    return {'dates':[str(pd.Timestamp(t).date()) for t in target['time'].values],
            'west_c':[float(x) for x in west.values],
            'east_c':[float(x) for x in east.values],
            'dmi_c':[float(x) for x in (west-east).values],
            'units':'degree_Celsius',
            'source_url':URL.format(y=TARGET)}


if __name__=='__main__':
    print(json.dumps(solve(),indent=2))
