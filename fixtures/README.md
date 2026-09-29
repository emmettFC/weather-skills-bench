# Frozen public inputs

Each Zip contains only the named Zarr stores for one task. There are no answer keys or reference recipes in these archives. Data are synthetic diagnostic fixtures, not observed or forecast weather products.

`manifest.json` records the SHA-256 of each archive and each store. Archive timestamps and permissions are fixed, so regenerating the same inputs produces identical bytes. Verify or inspect a fixture using Python alone:

```python
import hashlib, json, zipfile
from pathlib import Path
import xarray as xr

root = Path('fixtures')
entry = json.loads((root / 'manifest.json').read_text())['cases']['rainfall-completeness']
archive = root / entry['archive']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == entry['sha256']
with zipfile.ZipFile(archive) as source:
    source.extractall('/tmp/rainfall-case')
ds = xr.open_zarr('/tmp/rainfall-case/rain.zarr', chunks=None)
print(ds)
```

The case brief and output schema are in `cases/<case-id>.json`. To revise fixtures deliberately, update `weather_bench/cases.py`, run `python -m weather_bench.cli freeze`, and repeat both local and container reference validation.
