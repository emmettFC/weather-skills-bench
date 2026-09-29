"""Real forecast requests: agents begin with no downloaded weather data."""
import json
from .cases import Case,step
from .catalog import ROOT

SUITE='end-to-end-v1'
BBOX='5/34/-5/42'


def fetch(id,date,product,var):
    return step(id,'kenya-forecast-fetch','',id,'--dataset',product,'--date',date,'--bbox',BBOX,'--variable',var)


def plot(input,style='heatmap',title='ECMWF S2S Kenya rainfall (mm) · issue 2026-09-27',*extra):
    return step('figure','plot',input,'outlook.png','--style',style,'--title',title,*extra)


def e2e_cases():
    path=ROOT/'references/e2e/answers.json'
    if not path.exists():return []
    answers=json.loads(path.read_text());result=[]
    common=" Start from the public Kenya forecast archive; no weather data is preloaded. Use the service rectangle 5N/34E/5S/42E, including boundary grid centres (this is a rectangular service area, not a country-polygon average). Regional means use cosine-latitude weights and equal longitude weights. Include the control and every perturbed member with equal member weight. Write a labelled briefing figure to /work/outlook.png and return figure='/work/outlook.png'. Cite the exact raw source store URL(s) in the requested answer fields. Output fields follow source latitude/longitude order."
    sources=['Archive browser: https://kenya-forecasts.sheerwater.rhizaresearch.org/files/',
             'Public object listing: https://storage.googleapis.com/storage/v1/b/kenya-forecasting-data/o?prefix=2026-09-27/data/&delimiter=/',
             'Raw stores: https://storage.googleapis.com/kenya-forecasting-data/YYYY-MM-DD/data/ECMWF_s2s_precip_YYYY-MM-DD.zarr and ECMWF_s2s_daily_vars_YYYY-MM-DD.zarr. These are provider exports, not normalized skill outputs; inspect their metadata.',
             'The archive is an operationally published product. Pin the requested issue dates, not the latest available. Output describes the model outlook; it is not a warning or verification against eventual observations.']
    def add(id,title,brief,challenge,recipe,exports):
        producers={n['output']:n['id'] for n in recipe}
        edges=[(producers[p],n['id']) for n in recipe for p in n['inputs'] if p in producers]
        c=Case(id,title,brief+common,challenge,{},answers[id],recipe,exports,edges,(),SUITE,tuple(sources))
        result.append(c)
    rain=[fetch('forecast','2026-09-27','precip','tp'),step('weeks','aggregate-temporal','forecast','weeks','--period','weekly'),
          step('totals','convert-to-totals','weeks','totals'),step('map','summarize-dim','totals','map','--dim','number','--method','mean'),
          step('region','summarize-dim','totals','region','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
          step('median','summarize-dim','region','median','--dim','number','--method','median'),step('spread','summarize-dim','region','spread','--dim','number','--method','std'),plot('map')]
    add('e2e-kenya-rainfall','Kenya rainfall outlook: fetch, quantify uncertainty, and brief',
        "Prepare the six-week rainfall outlook from the ECMWF S2S issue of 2026-09-27. For each fully covered seven-day period from initialization, provide the ensemble-mean rainfall map and the median and sample spread (ddof=1) of regional rainfall totals across members. Return period_end_lead_days, ensemble_mean_mm [period][latitude][longitude], regional_median_mm, regional_spread_mm, latitude, longitude, units='mm', source_url, and figure. The figure should show the six forecast maps with period labels and rainfall units.",
        'Real archive discovery and retrieval, accumulation semantics, incomplete horizon, ensemble regional uncertainty, provenance and delivery.',rain,
        {'period_end_lead_days':('map','@days:step'),'ensemble_mean_mm':('map','tp'),'regional_median_mm':('median','tp'),'regional_spread_mm':('spread','tp'),'latitude':('map','latitude'),'longitude':('map','longitude'),'units':'mm','source_url':answers['e2e-kenya-rainfall']['source_url'],'figure':'/work/outlook.png'})
    revision=[]
    for label,date in [('current','2026-09-27'),('previous','2026-09-20')]:
        revision += [fetch(label,date,'precip','tp'),step(label+'_weeks','aggregate-temporal',label,label+'_weeks','--period','weekly'),
            step(label+'_totals','convert-to-totals',label+'_weeks',label+'_totals'),step(label+'_clock','step-to-time',label+'_totals',label+'_clock'),
            step(label+'_periods','select',label+'_clock',label+'_periods','--dim','time','--value','2026-10-04','--value','2026-10-11'),
            step(label+'_mean','summarize-dim',label+'_periods',label+'_mean','--dim','number','--method','mean')]
    revision += [step('change','difference','current_mean previous_mean','change'),step('region','summarize-dim','change','region','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),plot('change','heatmap','Weekly rainfall change (mm) · Sep 27 minus Sep 20 issue','--colormap','RdBu_r')]
    add('e2e-kenya-revision','Kenya forecast revision: compare the same future weeks',
        "Brief how the ECMWF S2S rainfall outlook changed between the 2026-09-20 and 2026-09-27 issues for the two civil periods 2026-09-27 00:00–2026-10-04 00:00 and 2026-10-04 00:00–2026-10-11 00:00. Return valid_period_end_dates (YYYY-MM-DD), current_mean_mm, previous_mean_mm, change_mm (current minus previous), each [period][latitude][longitude], regional_change_mm, latitude, longitude, units='mm', current_source_url, previous_source_url, and figure. Compare ensemble means; do not pair individual members across issues. The figure should show both change maps with signed differences and dates.",
        'Two actual issue dates; valid-time alignment instead of same lead; independent ensembles; change maps and source citations.',revision,
        {'valid_period_end_dates':('change','@dates:time'),'current_mean_mm':('current_mean','tp'),'previous_mean_mm':('previous_mean','tp'),'change_mm':('change','tp'),'regional_change_mm':('region','tp'),'latitude':('change','latitude'),'longitude':('change','longitude'),'units':'mm','current_source_url':answers['e2e-kenya-revision']['current_source_url'],'previous_source_url':answers['e2e-kenya-revision']['previous_source_url'],'figure':'/work/outlook.png'})
    heat=[fetch('forecast','2026-09-27','daily_vars','t2m'),step('region','summarize-dim','forecast','region','--dim','latitude','--dim','longitude','--method','mean','--lat-weighted'),
        step('peaks','aggregate-temporal','region','peaks','--period','weekly','--method','max'),step('fortnight','select','peaks','fortnight','--dim','step','--value','7D','--value','14D')]
    for id,method in [('median','median'),('spread','std'),('minimum','min'),('maximum','max')]:heat.append(step(id,'summarize-dim','fortnight',id,'--dim','number','--method',method))
    heat.append(plot('median','timeseries','Median hottest daily regional mean (°C) · issue 2026-09-27'))
    add('e2e-kenya-heat','Kenya heat outlook: uncertainty in the hottest regional day',
        "Prepare a two-week heat outlook from the 2026-09-27 ECMWF S2S issue. For each member and seven-day forecast period, consider the hottest daily regional-mean 2 m temperature (not daily maximum temperature and not the spatial mean of local peaks). Return period_end_lead_days=[7,14], median_peak_c, peak_spread_c (sample ddof=1), minimum_member_peak_c, maximum_member_peak_c, units='degree_Celsius', source_url, and figure. The figure should show median hottest-day temperature for both weeks with valid-period labels and Celsius units.",
        'Discover correct temperature product; raw Kelvin conversion; distinguish daily mean, spatial mean, and temporal maximum before ensemble uncertainty.',heat,
        {'period_end_lead_days':('median','@days:step'),'median_peak_c':('median','t2m'),'peak_spread_c':('spread','t2m'),'minimum_member_peak_c':('minimum','t2m'),'maximum_member_peak_c':('maximum','t2m'),'units':'degree_Celsius','source_url':answers['e2e-kenya-heat']['source_url'],'figure':'/work/outlook.png'})
    return result
