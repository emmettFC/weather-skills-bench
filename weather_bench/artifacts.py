"""Fixed answer serialization, never model-authored computation or case-aware extraction."""
import json
from pathlib import PurePosixPath


def validate_manifest(fields):
    if not isinstance(fields,dict) or not fields or len(fields)>30:
        raise ValueError('submit requires an object of answer fields')
    for key,spec in fields.items():
        if not isinstance(key,str): raise ValueError('Answer keys must be strings')
        if isinstance(spec,str): continue  # literal labels, e.g. units; never numeric answers
        if not isinstance(spec,dict) or set(spec)-{'artifact','variable','format','squeeze'}:
            raise ValueError('Each numeric/array field must reference a skill-produced artifact')
        path=PurePosixPath(spec.get('artifact',''))
        if not str(path).startswith('/work/') or '..' in path.parts or path.suffix!='.zarr':
            raise ValueError('Artifact must be a .zarr store under /work')
        if not isinstance(spec.get('variable'),str) or not spec['variable']:
            raise ValueError('An artifact variable or coordinate is required')
        if spec.get('format','values') not in ('values','dates','days'):
            raise ValueError('Only values, dates, and timedelta days formatting are supported')
        if 'squeeze' in spec and not isinstance(spec['squeeze'],bool):
            raise ValueError('squeeze must be a boolean')
    json.dumps(fields,allow_nan=False)
    return fields


# Runs inside the existing container, given only a validated JSON argument.
# No evaluation, formulas, selection, aggregation, or case-specific knowledge.
SERIALIZE_CODE='''import json, sys
from pathlib import Path
import xarray as xr
import numpy as np
fields=json.loads(sys.argv[1]); answer={}
for key,spec in fields.items():
    if isinstance(spec,str):
        answer[key]=spec; continue
    path=Path(spec['artifact']).resolve()
    if not path.is_relative_to('/work'): raise ValueError('Artifact escaped workspace')
    with xr.open_zarr(path,chunks=None) as ds:
        values=ds[spec['variable']].values
        fmt=spec.get('format','values')
        if fmt=='dates': value=[str(x)[:10] for x in values.reshape(-1)]
        elif fmt=='days': value=(values/np.timedelta64(1,'D')).tolist()
        else: value=(values.squeeze() if spec.get('squeeze',True) else values).tolist()
        answer[key]=value
text=json.dumps(answer,allow_nan=False)
assert len(text)<100000
Path('/work/answer.json').write_text(text)
print(text)
'''
