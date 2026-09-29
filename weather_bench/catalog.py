from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CATALOG=ROOT.parent/"weather-skills-catalog"
CORE_COMMIT="e118b9531181224cb1459efbd9f2b114117f0a79"


def inventory(catalog=DEFAULT_CATALOG):
    out={}
    for doc in sorted(Path(catalog).glob("skills/*/*/SKILL.md")):
        text=doc.read_text()
        scripts=list((doc.parent/"scripts").glob("*.py"))
        out[doc.parent.name]={"name":doc.parent.name,"provider":doc.parent.parent.name,
            "description":next(x.removeprefix("description:").strip().strip('"') for x in text.splitlines() if x.startswith("description:")),
            "doc":str(doc.relative_to(catalog)),"scripts":[str(s.relative_to(catalog)) for s in scripts],
            "sha256":hashlib.sha256(doc.read_bytes()).hexdigest()}
    return out


def script_for(name,catalog=DEFAULT_CATALOG):
    paths=inventory(catalog)[name]["scripts"]
    if len(paths)!=1:
        raise ValueError(f"Expected one script for {name}")
    return Path(catalog)/paths[0]


def tree_hash(path):
    digest=hashlib.sha256()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            digest.update(str(p.relative_to(path)).encode()+b"\0"+p.read_bytes())
    return digest.hexdigest()


def lock(catalog=DEFAULT_CATALOG):
    return {"catalog_commit":subprocess.check_output(["git","-C",str(catalog),"rev-parse","HEAD"],text=True).strip(),
            "catalog_tree_sha256":tree_hash(Path(catalog)/"skills"),"core_commit":CORE_COMMIT,
            "skills":inventory(catalog)}


def verify(catalog=DEFAULT_CATALOG):
    pinned=json.loads((ROOT/"catalog.lock.json").read_text())
    current=lock(catalog)
    if pinned!=current:
        raise RuntimeError("Catalog differs from catalog.lock.json; explicitly rebuild/revalidate before running a study")
    return pinned
