"""Static results and sanitized, allowlisted execution logs for human auditing."""
import json
import os
import re
from .catalog import ROOT
from .cases import cases
from .health import study_health, atomic_json
from datetime import datetime, timezone

MODEL_PROFILES={
    "anthropic/claude-sonnet-4.6":{"label":"Claude Sonnet 4.6","weights":"Closed","category":"Premium"},
    "google/gemini-2.5-flash":{"label":"Gemini 2.5 Flash","weights":"Closed","category":"Economy"},
    "deepseek/deepseek-v3.2":{"label":"DeepSeek V3.2","weights":"Open","category":"Large MoE"},
    "qwen/qwen3-30b-a3b-instruct-2507":{"label":"Qwen3 30B A3B","weights":"Open","category":"Compact MoE"}}
MODEL_PROFILES.update({
    "meta-llama/llama-3.2-1b-instruct":{"label":"Llama 3.2 1B","weights":"Open","category":"Small"},
    "meta-llama/llama-3.2-3b-instruct":{"label":"Llama 3.2 3B","weights":"Open","category":"Small"},
    "anthropic/claude-fable-5.1":{"label":"Claude Fable 5.1","weights":"Closed","category":"Frontier"},
    "openai/gpt-6-astra":{"label":"GPT-6 Astra","weights":"Closed","category":"Frontier"},
    "anthropic/claude-sonnet-5.5":{"label":"Claude Sonnet 5.5","weights":"Closed","category":"Premium"},
    "google/gemini-3.1-flash-lite":{"label":"Gemini 3.1 Flash-Lite","weights":"Closed","category":"Economy"},
    "deepseek/deepseek-v4.1-flash":{"label":"DeepSeek V4.1 Flash","weights":"Open","category":"Large MoE"},
    "qwen/qwen3.5-9b":{"label":"Qwen3.5 9B","weights":"Open","category":"Small"}})


def public_text(value):
    """Remove credential-shaped strings and host/account identifiers from log text.

    This is defense in depth: evaluation containers never receive credentials.
    Never export an API envelope, headers, or hidden reasoning in the first place.
    """
    text=str(value)
    text=re.sub(r"(?i)Bearer\s+[^\s\"']+", "Bearer [REDACTED]", text)
    text=re.sub(r"\b(?:sk-(?:or-v1-)?|org_|user_)[A-Za-z0-9_-]{8,}", "[REDACTED]", text)
    text=re.sub(r"(?i)((?:api[_-]?key|access[_-]?token|authorization)[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]+", r"\1[REDACTED]", text)
    text=text.replace(str(ROOT), "[BENCHMARK]")
    return re.sub(r"/(?:Users|home)/[^/\s\"']+", "/[USER]", text)


def public_event(event):
    result={k:event[k] for k in ("action","skill","args","returncode","seconds","turn") if k in event}
    if "fields" in event:
        result["fields"]=json.loads(public_text(json.dumps(event["fields"])))
    for key in ("code","stdout","stderr","message"):
        if key in event:
            result[key]=public_text(event[key])
    if "args" in result:
        result["args"]=[public_text(arg) for arg in result["args"]]
    if event.get("action")=="api_error":
        # Provider envelopes can contain account IDs. Expose a compact diagnosis.
        try:
            envelope=json.loads(event.get("message", ""))
            error=envelope.get("error", envelope)
            metadata=error.get("metadata") or {}
            result["message"]=public_text(" · ".join(str(x) for x in (
                error.get("code"),error.get("message"),metadata.get("provider_name"),
                metadata.get("provider_error_code"),metadata.get("limit_source")) if x is not None))
        except (ValueError,AttributeError):
            pass
    return result


def effective_status(run,config):
    """The shared task deadline can expire during an in-flight HTTP request.

    Preserve the raw transport status separately; classify a measured exhaustion
    of the overall task budget as a task timeout, not a provider-only exclusion.
    """
    if (config.get("hard_request_deadline") and run["status"]=="api_error"
            and run["solve_seconds"]>=config["task_timeout_seconds"]
            and any(e.get("action")=="api_error" and e.get("message")=="ReadTimeout"
                    for e in run.get("events",[]))):
        return "task_timeout"
    return run["status"]


def public_audit(run):
    calls=[]; instructions=None
    raw_dir=ROOT/"results/raw"/run["run_id"]
    for index,request in enumerate(run.get("requests", [])):
        usage=request.get("usage") or {}
        call={"number":index+1,"provider":request.get("provider"),
              "model":request.get("resolved_model"),"seconds":request.get("seconds"),
              "finish_reason":request.get("finish_reason"),
              "usage":{k:usage.get(k) for k in ("prompt_tokens","completion_tokens","total_tokens","cost")}}
        call["usage"]["cached_tokens"]=(usage.get("prompt_tokens_details") or {}).get("cached_tokens",0)
        call["usage"]["reasoning_tokens"]=(usage.get("completion_tokens_details") or {}).get("reasoning_tokens",0)
        path=raw_dir/f"{index:03d}.json"
        if path.exists():
            raw=json.loads(path.read_text())
            choices=raw.get("response",{}).get("choices") or []
            # Visible assistant output only. Deliberately omit reasoning fields.
            content=(choices[0].get("message") or {}).get("content") if choices else None
            call["response"]=public_text(content) if isinstance(content,str) else None
            if index==0:
                instructions=next((public_text(m["content"]) for m in raw.get("request",{}).get("messages",[])
                                   if m.get("role")=="system" and isinstance(m.get("content"),str)),None)
            messages=raw.get("request",{}).get("messages",[])
            if messages and messages[-1].get("role")=="user":
                feedback=messages[-1].get("content","")
                if isinstance(feedback,str) and feedback.startswith("Execution observation:\n"):
                    call["input_observation"]=public_text(feedback.removeprefix("Execution observation:\n"))
        calls.append(call)
    return {"version":1,"model_calls":calls,"instructions":instructions,
            "events": [public_event(e) for e in run.get("events",[])],
            "note":(run.get("recovery",{}).get("note","")+" ")+"Recorded execution output is bounded by the runner (stdout 16,000 characters; stderr last 8,000). Visible model responses only; hidden reasoning, API envelopes, credentials and account identifiers are excluded. Model calls and execution events are separate ordered logs, not a reconstructed timestamp alignment."}


def export_dashboard():
    reference_path=ROOT/"results/reference.json"
    reference=json.loads(reference_path.read_text()) if reference_path.exists() else {"runs":[]}
    case_map={c.id:c for c in cases()}
    tasks=[]
    for case in case_map.values():
        ref=next((r for r in reference["runs"] if r["case_id"]==case.id),None)
        tasks.append({**case.public(),"expected":case.expected,"challenge":case.challenge,
                      "oracle_verified":bool(ref and (ref.get('oracle_verified') or ref['correctness']['passed'])),
                      "reference_figure":f'artifacts/reference/{case.id}.png' if ref and ref.get('figure',{}).get('passed') else None,
                      "catalog_reference_error":ref.get('error') if ref else None,
                      "reference_passed":bool(ref and ref["correctness"]["passed"]),
                      "recipe":[{"id":n["id"],"skill":n["skill"],"args":n["args"]} for n in case.recipe],
                      "edges":case.edges})
    quality_path=ROOT/"results/e2e-quality.json"
    quality=json.loads(quality_path.read_text()) if quality_path.exists() else None
    sensitivity_path=ROOT/"results/rainfall-semantics-audit.json"
    sensitivity=json.loads(sensitivity_path.read_text()) if sensitivity_path.exists() else {}
    sensitivity_runs={r["run_id"]:r for r in sensitivity.get("runs",[])}
    studies=[]
    for path in sorted((ROOT/"results/studies").glob("*.json")):
        s=json.loads(path.read_text()); runs=[]
        if s.get("kind")=="harness-smoke":
            continue
        for r in s["runs"]:
            runs.append({k:r[k] for k in ("run_id","case_id","model","arm","rep","status","answer","correctness","workflow","usage","solve_seconds","setup_seconds","wall_seconds","llm_seconds","execution_seconds","input_sha256","image_ids")})
            runs[-1]["original_status"]=r["status"]
            if r["run_id"] in sensitivity_runs:runs[-1]["sensitivity_audit"]=sensitivity_runs[r["run_id"]]
            for key in ('scientific_correctness','figure','source_versions','network_events','recovery'):
                if key in r:runs[-1][key]=r[key]
            runs[-1]["status"]=effective_status(r,s["config"])
            runs[-1]["trace"]=[{"action":e["action"],"skill":e.get("skill"),"args":e.get("args"),"returncode":e.get("returncode"),"seconds":e.get("seconds",0)} for e in r["events"]]
            runs[-1]["providers"]=sorted({q["provider"] for q in r["requests"] if q.get("provider")})
            runs[-1]["audit"]=public_audit(r)
        studies.append({"study_id":s["study_id"],"kind":s["kind"],"started_at":s["started_at"],
                        "quality":quality if quality and s["config"].get("protocol_version")==quality["protocol_version"] else None,"health":study_health(s),"finished_at":s.get("finished_at"),"planned_runs":s["planned_runs"],"runs":runs,
                        "catalog_commit":s["catalog_commit"],"ledger":s["ledger"],
                        "resumed_from":s.get("resumed_from"),"resume_note":s.get("resume_note"),
                        "diagnostics":{"provider_failures":len(s.get("infrastructure_runs",[])),
                            "interruption":s.get("interruption"),"excluded_models":s.get("excluded_models",{}),
                            "supplementary_runs":len(s.get("supplementary_runs",[]))},
                        "config":{k:v for k,v in s["config"].items() if k!="model_metadata"}})
    published=ROOT/"results/published"; published.mkdir(exist_ok=True)
    for s in studies:
        (published/f"{s['study_id']}.json").write_text(json.dumps(s,indent=2,allow_nan=False)+"\n")
    available={s["study_id"]:s for s in studies}
    for path in published.glob("*.json"):
        s=json.loads(path.read_text()); available.setdefault(s["study_id"],s)
    studies=[available[k] for k in sorted(available)]
    from .statistics import paired_summary,condition_summary
    for s in studies:
        s["paired_statistics"]=paired_summary(s["runs"],"skills_only" if "skills_only" in s["config"]["arms"] else "skills",len(s["config"]["models"]))
        s["condition_statistics"]=condition_summary(s["runs"])
        s["task_outcome_statistics"]=condition_summary(s["runs"],include_provider_errors=False)
    payload={"exported_at":datetime.now(timezone.utc).isoformat(),"schema_version":2,"cases":tasks,"studies":studies,"model_profiles":MODEL_PROFILES,
             "catalog_commit":reference.get("catalog_commit"),"core_commit":reference.get("core_commit")}
    docs=ROOT/"docs"; docs.mkdir(exist_ok=True)
    # JS rather than fetch() also permits opening index.html directly from disk.
    js_temp=docs/f"data.{os.getpid()}.tmp.js"
    js_temp.write_text("window.BENCHMARK_DATA = "+json.dumps(payload,indent=2,allow_nan=False)+";\n")
    js_temp.replace(docs/"data.js")
    atomic_json(docs/"data.json",payload)
    return docs/"index.html"
