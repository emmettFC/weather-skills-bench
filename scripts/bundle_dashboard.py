"""Build one portable HTML snapshot from the public dashboard export.

Usage: .venv/bin/python scripts/bundle_dashboard.py [--output FILE]
Only public assets are read; no credentials or private result journals are loaded.
"""
import argparse
import base64
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def script_json(value):
    # Model logs can contain HTML, including script end tags. Keep them data.
    return json.dumps(value, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')


def bundle(output):
    docs = ROOT / 'docs'
    data = json.loads((docs / 'data.json').read_text())
    assets = {}
    def collect(value):
        if isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
        elif isinstance(value, str) and value.startswith('artifacts/'):
            path = (docs / value).resolve()
            if not path.is_relative_to((docs / 'artifacts').resolve()):
                raise ValueError('Asset path escapes artifacts directory')
            if value not in assets:
                mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
                assets[value] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
    collect(data)
    bootstrap = '''
window.BENCHMARK_SNAPSHOT = true;
window.BENCHMARK_DATA = DATA_PLACEHOLDER;
const BUNDLED_ASSETS = ASSETS_PLACEHOLDER;
const BUNDLE_URLS = new Map();
const BUNDLE_EXPORT_ASSETS = new Map();
window.BENCHMARK_ASSET_EXPORT = BUNDLE_EXPORT_ASSETS;
for (const [path,uri] of Object.entries(BUNDLED_ASSETS)) {
  const [header,payload] = uri.split(',');
  const bytes = Uint8Array.from(atob(payload), c=>c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], {type:header.slice(5).split(';')[0]}));
  BUNDLE_URLS.set(path,url);BUNDLE_EXPORT_ASSETS.set(url,uri);
}
function resolveBundledAssets(value) {
  if(Array.isArray(value))return value.map(resolveBundledAssets);
  if(value && typeof value==='object'){
    for(const key of Object.keys(value))value[key]=resolveBundledAssets(value[key]);
    return value;
  }
  return BUNDLE_URLS.get(value) || value;
}
resolveBundledAssets(window.BENCHMARK_DATA);
'''.replace('DATA_PLACEHOLDER', script_json(data)).replace('ASSETS_PLACEHOLDER', script_json(assets))
    enhance = '''
document.getElementById('methodology-link').addEventListener('click', event=>{
  event.preventDefault();showDetail('Methodology', '<pre>'+esc(METHODOLOGY_PLACEHOLDER)+'</pre>');
});
document.getElementById('export-data').addEventListener('click', event=>{
  event.preventDefault();
  const portable = JSON.stringify(DATA, (key,value)=>BUNDLE_EXPORT_ASSETS.get(value) || value, 2);
  const url=URL.createObjectURL(new Blob([portable], {type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='weather-skills-benchmark.json';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
'''.replace('METHODOLOGY_PLACEHOLDER', script_json((ROOT / 'METHODOLOGY.md').read_text()))
    html = (docs / 'index.html').read_text()
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>'+(docs / 'style.css').read_text()+'</style>')
    html = html.replace('<script src="data.js"></script>', '<script>'+bootstrap+'</script>')
    app = (docs / 'app.js').read_text().replace('</script', '<\\/script')
    html = html.replace('<script src="app.js"></script>', '<script>'+app+'</script><script>'+enhance+'</script>')
    html = html.replace('<a href="https://github.com/jataware/weather-skills-bench/blob/main/METHODOLOGY.md">Methodology ↗</a>', '<a id="methodology-link" href="#methodology">Methodology</a>')
    html = html.replace('<a href="data.json" download>', '<a id="export-data" href="#export" download>')
    stamp = data.get('exported_at', 'unknown')
    html = html.replace('<span>Weather Skills Benchmark</span>', '<span>Offline snapshot · '+stamp+'</span>')
    output = Path(output).resolve()
    protected = {docs / name for name in ('index.html','app.js','style.css','data.js','data.json')}
    if output in protected:
        raise ValueError('Output must not overwrite a source dashboard asset')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    return {'path':str(output), 'bytes':output.stat().st_size, 'embedded_images':len(assets), 'snapshot_at':stamp}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/weather-skills-benchmark.html')
    args = parser.parse_args()
    print(json.dumps(bundle(args.output), indent=2))
