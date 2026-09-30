"""Observational end-to-end requests: agents begin with no downloaded weather data.

Separate from e2e_cases because the source is NOAA PSL OPeNDAP rather than the
Kenya object archive, and because the answer is an observed index rather than a
model outlook.
"""
import json
from .cases import Case, step
from .catalog import ROOT

SUITE='end-to-end-v1'
BOX='11/49/-11/111'                  # union of both dipole boxes, with a margin
CLIM_YEARS=range(2013,2023)
WEST='10/50/-10/70'
EAST='0/90/-10/110'


def fetch(id,year):
    return step(id,'oisst-fetch','',id,'--start-time',f'{year}-10-01','--end-time',f'{year}-10-07','--bbox',BOX)


def obs_cases():
    path=ROOT/'references/obs/answers.json'
    if not path.exists():return []
    answers=json.loads(path.read_text())
    sources=[
      'NOAA PSL OPeNDAP: https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.YYYY.nc, one file per calendar year.',
      'OISST v2.1 is a 0.25 degree global analysis. Grid centres sit at 0.125 + 0.25k, so neither 10.0 degrees latitude nor 50.0 degrees longitude is a cell centre. Resolving the closed intervals to centres gives an 80 by 80 western box and a 40 by 80 eastern box.',
      'The eastern box covers Sumatra and Java. 399 of its 3200 cells are land and carry no value.',
      '2023 fields are final. OISST revises for about two weeks after real time, so these dates are stable.',
      'October 2023 was a strong positive dipole event. An index near zero indicates the anomaly step was skipped.']
    recipe=[fetch(f'clim{y}',y) for y in CLIM_YEARS]+[
      step('climstack','concat',' '.join(f'clim{y}' for y in CLIM_YEARS),'climstack','--dim','time'),
      step('climatology','summarize-dim','climstack','climatology','--dim','time','--method','mean'),
      fetch('target',2023),
      step('anomaly','difference','target climatology','anomaly'),
      step('westbox','clip-region','anomaly','westbox','--bbox',WEST),
      step('eastbox','clip-region','anomaly','eastbox','--bbox',EAST),
      step('west','summarize-dim','westbox','west','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
      step('east','summarize-dim','eastbox','east','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
      step('dmi','difference','west east','dmi'),
      step('figure','plot-timeseries','west east dmi','outlook.png','--variable','sst',
           '--title','Observed Indian Ocean Dipole, 1-7 October 2023 (degree_Celsius)')]
    brief=("Compute the observed Indian Ocean Dipole Mode Index for each day from 2023-10-01 to 2023-10-07 inclusive, "
      "from NOAA OISST v2.1 daily sea-surface temperature. No weather data is preloaded. Build a per-grid-cell "
      "climatology as the arithmetic mean of sea-surface temperature over 1-7 October in each of the ten years 2013 "
      "to 2022, seventy daily fields in total. Subtract that climatology field from each target day's field to obtain "
      "anomalies. Average the anomalies over a western box 50-70E, 10S-10N and an eastern box 90-110E, 10S-0, using "
      "cosine-latitude weights and equal longitude weights. A grid cell belongs to a box when its centre lies inside "
      "the closed interval. The analysis is missing over land, so exclude missing cells and renormalise the weights "
      "over the valid cells of each box. Return dates (YYYY-MM-DD) in ascending order, west_c, east_c, "
      "dmi_c=west_c-east_c, units='degree_Celsius', source_url citing the exact raw store(s) used, and figure. "
      "Write a labelled figure to /work/outlook.png showing the western anomaly, the eastern anomaly and the "
      "dipole index across the seven days, and return figure='/work/outlook.png'.")
    challenge=('The two boxes have different latitude extents, the eastern box is an eighth land so a mean that does '
      'not skip missing cells returns nothing, the climatology spans ten separate October weeks rather than one '
      'contiguous range, and it is a spatial field that must broadcast across the target days.')
    exports={'dates':('target','@dates:time'),'west_c':('west','sst'),'east_c':('east','sst'),
             'dmi_c':('dmi','sst'),'units':'degree_Celsius',
             'source_url':answers['iod-dmi-observed']['source_url'],'figure':'/work/outlook.png'}
    producers={n['output']:n['id'] for n in recipe}
    edges=[(producers[p],n['id']) for n in recipe for p in n['inputs'] if p in producers]
    return [Case('iod-dmi-observed',
      'Observed Indian Ocean Dipole from OISST: build a climatology and index a real event',
      brief,challenge,{},answers['iod-dmi-observed'],recipe,exports,edges,(),SUITE,tuple(sources))]
