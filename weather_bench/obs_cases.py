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
      brief,challenge,{},answers['iod-dmi-observed'],recipe,exports,edges,(),SUITE,tuple(sources)),
      skill_case(answers)]

SKILL_CLIM=range(2013,2023)
VERIFY=['2023-10-0'+str(d) for d in range(2,9)]


def swindow(id,year):
    return step(id,'oisst-fetch','',id,'--start-time',f'{year}-09-24','--end-time',f'{year}-10-08','--bbox',BOX)


def skill_case(answers):
    """Build two persistence forecasts of the dipole and score them against what happened."""
    recipe=[swindow(f'y{y}',y) for y in SKILL_CLIM]+[
      step('climstack','concat',' '.join(f'y{y}' for y in SKILL_CLIM),'climstack','--dim','time'),
      step('climatology','summarize-dim','climstack','climatology','--dim','time','--method','mean'),
      swindow('window',2023),
      step('anomaly','difference','window climatology','anomaly'),
      step('westbox','clip-region','anomaly','westbox','--bbox',WEST),
      step('eastbox','clip-region','anomaly','eastbox','--bbox',EAST),
      step('west','summarize-dim','westbox','west','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
      step('east','summarize-dim','eastbox','east','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
      step('dmi','difference','west east','dmi'),
      # A single --value collapses the time dim and drops the scalar coord, which is
      # what lets the held forecast broadcast over the verification week. Kept as a
      # labelled selection so an inner join cannot silently return nothing.
      step('early','select','dmi','early','--dim','time','--value','2023-09-24'),
      step('late','select','dmi','late','--dim','time','--value','2023-10-01'),
      step('observed','select','dmi','observed','--dim','time',*[a for d in VERIFY for a in ('--value',d)]),
      step('errearly','difference','early observed','errearly'),
      step('errlate','difference','late observed','errlate'),
      step('biasearly','summarize-dim','errearly','biasearly','--dim','time','--method','mean'),
      step('biaslate','summarize-dim','errlate','biaslate','--dim','time','--method','mean'),
      step('figure','plot-timeseries','observed errearly errlate','outlook.png','--variable','sst',
           '--title','Dipole persistence forecasts against observations, 2-8 October 2023 (degree_Celsius)')]
    brief=("Build two persistence forecasts of the observed Indian Ocean Dipole Mode Index and score them against "
      "what happened. No weather data is preloaded. Use NOAA OISST v2.1 daily sea-surface temperature. Build a "
      "per-grid-cell climatology as the arithmetic mean of sea-surface temperature over 24 September to 8 October "
      "in each of the ten years 2013 to 2022, and subtract it to obtain anomalies. Average the anomalies over a "
      "western box 50-70E, 10S-10N and an eastern box 90-110E, 10S-0 using cosine-latitude weights and equal "
      "longitude weights, and take the index as west minus east. A grid cell belongs to a box when its centre lies "
      "inside the closed interval. The analysis is missing over land, so exclude missing cells and renormalise the "
      "weights over the valid cells of each box. A persistence forecast holds the index value observed on its issue "
      "date constant over the whole verification period. Issue one forecast on 2023-09-24 and another on "
      "2023-10-01, and verify both against the observed index on each of 2023-10-02 to 2023-10-08 inclusive. "
      "Define error as forecast minus observed, and bias as the mean error over the seven verification days. "
      "Return dates (YYYY-MM-DD) in ascending order, observed_dmi_c, forecast_early_c and forecast_late_c (the two "
      "held values), error_early_c and error_late_c, bias_early_c and bias_late_c, units='degree_Celsius', "
      "source_url citing the exact raw store(s) used, and figure. Write a labelled figure to /work/outlook.png "
      "showing the observed index and the error of each forecast across the seven days, and return "
      "figure='/work/outlook.png'.")
    challenge=('A held forecast is a scalar that must broadcast over the verification week, so a selection that '
      'leaves a time coordinate in place aligns to nothing. The two issues sit at different leads, the error sign '
      'convention decides whether the forecasts look too high or too low, and the eastern box is an eighth land.')
    sources=[
      'NOAA PSL OPeNDAP: https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.YYYY.nc, one file per calendar year.',
      'OISST v2.1 is a 0.25 degree global analysis. Grid centres sit at 0.125 + 0.25k, so neither 10.0 degrees latitude nor 50.0 degrees longitude is a cell centre.',
      'The eastern box covers Sumatra and Java and is roughly an eighth land.',
      '2023 fields are final, so the verification is stable.',
      'The dipole was strengthening through early October 2023, so a forecast held from an earlier date is expected to sit below what was observed.']
    exports={'dates':('observed','@dates:time'),'observed_dmi_c':('observed','sst'),
      'forecast_early_c':('early','sst'),'forecast_late_c':('late','sst'),
      'error_early_c':('errearly','sst'),'error_late_c':('errlate','sst'),
      'bias_early_c':('biasearly','sst'),'bias_late_c':('biaslate','sst'),
      'units':'degree_Celsius','source_url':answers['iod-persistence-skill']['source_url'],
      'figure':'/work/outlook.png'}
    producers={n['output']:n['id'] for n in recipe}
    edges=[(producers[p],n['id']) for n in recipe for p in n['inputs'] if p in producers]
    return Case('iod-persistence-skill',
      'Persistence forecasts of the Indian Ocean Dipole, scored against what happened',
      brief,challenge,{},answers['iod-persistence-skill'],recipe,exports,edges,(),SUITE,tuple(sources))

