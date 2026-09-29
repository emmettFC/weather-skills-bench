"""Deterministic answer checks and externally observed workflow conformance."""
import math
from collections import Counter


def grade(expected, actual, atol=1e-6, rtol=1e-6):
    failures=[]

    def compare(want,got,path):
        if isinstance(want,dict):
            if not isinstance(got,dict) or set(want)!=set(got):
                failures.append(f"{path}: expected exactly keys {sorted(want)}")
                return
            for key in want:
                compare(want[key],got[key],f"{path}.{key}")
        elif isinstance(want,list):
            if not isinstance(got,list) or len(want)!=len(got):
                failures.append(f"{path}: expected array length {len(want)}")
                return
            for i,(a,b) in enumerate(zip(want,got)):
                compare(a,b,f"{path}[{i}]")
        elif isinstance(want,str):
            if got!=want:
                failures.append(f"{path}: wrong string")
        else:
            try:
                valid=not isinstance(got,bool) and isinstance(got,(int,float)) and math.isfinite(got) and math.isclose(float(want),got,abs_tol=atol,rel_tol=rtol)
            except (OverflowError,TypeError,ValueError):
                valid=False
            if not valid: failures.append(f"{path}: numeric mismatch")

    compare(expected,actual,"answer")
    return {"passed":not failures,"failures":failures}


ALIASES={"-i":"--input","-o":"--output","-v":"--variable"}


def flags(args):
    """Preserve repeated flags and normalize common aliases and --key=value."""
    result={}; i=0
    while i<len(args):
        flag=args[i]; i+=1
        if "=" in flag:
            flag,value=flag.split("=",1)
        elif i<len(args) and not args[i].startswith("--") and args[i] not in ALIASES:
            value=args[i]; i+=1
        else:
            value=True
        key=ALIASES.get(flag,flag)
        result.setdefault(key,[]).append(value)
        if key=="--input":
            while i<len(args) and not args[i].startswith("-"):
                result[key].append(args[i]); i+=1
    return result


def workflow(case, events):
    """Match a reference partial order with artifact ancestry, not a flat name list.

    This measures reference-recipe conformance, not scientific correctness or proof
    that the final JSON was derived from the artifacts. Those are separate claims.
    Accept independent branch reordering; required argument values remain explicit.
    """
    calls=[e for e in events if e.get("action")=="skill" and e.get("returncode")==0]
    candidates={}
    parents={}
    version=0
    observed=[]
    for e in calls:
        f=flags(e["args"])
        inputs=[parents.get(p,{p}) for p in f.get("--input",[])]
        ancestry=set().union(*inputs) if inputs else set()
        token=f"event:{version}"; version+=1
        ancestry.add(token)
        for output in f.get("--output",[]):
            parents[output]=ancestry.copy()
        observed.append((e,f,token,ancestry))
    for node in case.recipe:
        need=flags(node["args"])
        if node['skill']=='plot':
            # Presentation wording/palette are not scientific dependencies.
            need.pop('--title',None)
            need.pop('--colormap',None)
        candidates[node["id"]]=[i for i,(e,f,_,_) in enumerate(observed)
            if e["skill"]==node["skill"] and all(not (Counter(v)-Counter(f.get(k,[]))) for k,v in need.items())]
    nodes=[n["id"] for n in case.recipe]
    solutions=[]

    def search(mapping,used):
        if len(mapping)==len(nodes):
            solutions.append(mapping.copy()); return True
        node=nodes[len(mapping)]
        for i in candidates[node]:
            if i in used:
                continue
            m={**mapping,node:i}
            valid=True
            for a,b in case.edges:
                if a in m and b in m:
                    valid &= m[a]<m[b] and observed[m[a]][2] in observed[m[b]][3]
            if valid and search(m,used|{i}):
                return True
        return False

    search({},set())
    prohibited=[e["skill"] for e in events if e.get("action")=="skill" and e["skill"] in case.forbidden]
    return {"passed":bool(solutions) and not prohibited,
            "matched_nodes":{k:bool(v) for k,v in candidates.items()},
            "dependency_edges":case.edges,"forbidden_calls":prohibited,
            "successful_skill_calls":len(calls),
            "scope":"reference recipe conformance; alternative correct algorithms may differ"}
