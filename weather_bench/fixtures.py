"""Freeze public inputs in byte-stable archives, with per-store content hashes."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
from .catalog import ROOT, tree_hash
from .cases import cases, write_inputs


def freeze():
    target=ROOT/"fixtures"; target.mkdir(exist_ok=True)
    manifest={"version":1,"kind":"synthetic diagnostic inputs","cases":{}}
    for case in cases():
        with tempfile.TemporaryDirectory() as temp:
            write_inputs(case,temp)
            path=target/f"{case.id}.zip"
            with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_STORED) as archive:
                for source in sorted(Path(temp).rglob("*")):
                    if source.is_file():
                        entry=zipfile.ZipInfo(str(source.relative_to(temp)),date_time=(1980,1,1,0,0,0))
                        entry.external_attr=0o100644<<16
                        archive.writestr(entry,source.read_bytes())
            manifest["cases"][case.id]={"archive":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "stores":{name:tree_hash(Path(temp)/f"{name}.zarr") for name in case.datasets}}
    (target/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


def verify_inputs(case,inputs):
    manifest=json.loads((ROOT/"fixtures/manifest.json").read_text())
    expected=manifest["cases"][case.id]["stores"]
    actual={name:tree_hash(Path(inputs)/f"{name}.zarr") for name in case.datasets}
    if actual!=expected:
        raise RuntimeError(f"Frozen input hash mismatch for {case.id}; regenerate and revalidate explicitly")


def materialize(case,destination):
    """Use the checked-in bytes rather than re-encoding inputs during a model run."""
    manifest=json.loads((ROOT/"fixtures/manifest.json").read_text())
    entry=manifest["cases"][case.id]
    archive=ROOT/"fixtures"/entry["archive"]
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=entry["sha256"]:
        raise RuntimeError(f"Archive hash mismatch: {case.id}")
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for name in source.namelist():
            parts=Path(name).parts
            if Path(name).is_absolute() or ".." in parts or not parts or parts[0] not in {k+".zarr" for k in case.datasets}:
                raise RuntimeError("Unexpected fixture archive member")
        source.extractall(destination)
    verify_inputs(case,destination)
