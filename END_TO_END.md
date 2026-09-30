# End-to-end forecast benchmark

The original ten tasks use synthetic data and remain useful component diagnostics. They do not establish the value of an end-to-end forecasting assistant. This suite uses **real archived ECMWF forecasts published through the Kenya forecast service**. Agents start with an empty input directory and must retrieve the requested issue, interpret it, calculate the requested product, produce a figure, and cite the exact source store.

The three initial requests are Kenya rainfall outlooks, a rainfall outlook revision, and a regional heat outlook. This is a first real-data cohort, not comprehensive coverage of African forecasting operations or a test of LLMs generating numerical weather predictions. These tasks assess faithful use of published forecasts; verifying those forecasts against later observed weather is a different evaluation.

## Cases and reference evidence

| Case | Deliverable | Independent Python witness | Catalog reference |
|---|---|---|---|
| Six-week rainfall outlook | Six ensemble-mean rainfall maps, regional member medians and spreads, source citation | Pass | Pass |
| Forecast revision | Compare Sep 27 and Sep 20 issues for the same two future weeks; change maps and regional changes | Pass | Pass |
| Two-week heat outlook | Uncertainty in each week's hottest daily regional-mean temperature, plot and citation | Pass | Fails at weighted Celsius mean |

All forecasts are real, from the September 27, 2026 issue, plus September 20 for the revision task. The issue dates are part of the immutable case definition. The rectangle 5N/34E/5S/42E is an explicitly specified service area, not a country-polygon statistic. Both conditions receive the same public source documentation and output definitions; neither receives preprocessed weather data, the reference recipe, a coordinate inventory, or private challenge hints.

The catalog reference runs the pinned, unmodified scripts. The independent oracle reads the provider's raw archive: it checks precipitation units, differences raw cumulative rainfall, integrates the requested windows, aligns issue dates, and calculates summaries without using weather-skills-core. A separate ordinary Python program successfully retrieves live data and produces the answers and figures in the Python-only container. Reference results are **not model performance results**.

### Known catalog limitation retained before model runs

`summarize-dim --lat-weighted` fails on the fetched Celsius temperature array with `pint.errors.OffsetUnitCalculusError`. The failure arises when dividing the weighted sum by the sum of weights. This is a catalog/runtime defect in the reference route, not evidence that a model failed meteorological reasoning. We did not change the scientific weighting, remove the case, modify the pinned catalog, or give the skills arm arbitrary code to hide it. A model that finds another correct route can still pass. Overall end-to-end success measures the combined agent-and-catalog system; it must not be described as a pure comparison of model reasoning. Report the heat case separately when interpreting model differences.

## Reproducibility and scoring

- Exact raw Zarr objects are preserved in three `fixtures/real-source-*.zip` archives. `fixtures/real-sources.json` records source URLs, GCS generation identifiers, byte lengths and SHA256 hashes for all 149 objects (about 4.2 MB of source content).
- `references/e2e/oracle.py` restores and verifies those bytes and recomputes the deterministic answer key offline. Agents never receive these archives or answers as mounted inputs.
- Live source generations are checked before and after each attempt. A change or unverified post-run version makes the result unscored (`source_changed`), rather than treating changed data as a model error. Pre-run unavailability stops the study before another paid attempt.
- Scientific answers require exact keys, shapes, dates and citations; numeric tolerances are absolute `1e-4` and relative `1e-6`. The tolerance accommodates float32 source arithmetic and is far smaller than reporting precision.
- PNG delivery requires a readable, nonblank image of at least 400×250 pixels. This is a deterministic delivery check, **not an automated judgment of whether the plotted values, labels or interpretation are scientifically correct**. The dashboard shows the image for human review and exposes numeric correctness separately.
- Recipe conformance checks successful calls and artifact dependencies. It is separate from answer correctness; a scientifically correct alternative can differ from the reference.
- Tests explicitly reject same-lead comparison of different issue dates, summing cumulative amounts directly, and spatial averaging of local temperature maxima in place of the maximum of the regional time series.

The raw snapshot supports reproducible ground truth today. A full agent replay against an offline HTTP mirror is **not implemented**; the model study below performs live downloads from pinned archives. Do not label it an offline replay experiment.

## Conditions, timing, and isolation

Both conditions have equal 40-response/40-execution limits, 350,000 cumulative tokens, 220,000 context bytes, a 20-minute task deadline and a four-minute execution deadline. The skills-only arm must read guides before invoking them and cannot run model-written code. The Python arm has scientific Python, HTTP and plotting libraries and can inspect, execute, receive errors and retry.

Separate `e2e-v1` images add the fetch and plot dependencies without changing the original diagnostic images. Both images contain the same static basemap assets. Forecast data and work directories are never shared across runs. An internal Docker network permits outbound HTTPS only through a proxy restricted to `storage.googleapis.com` and `naturalearth.s3.amazonaws.com`. The Python container has no skills installation; neither condition receives the OpenRouter key. Isolation checks verified source access, blocked arbitrary hosts and blocked direct egress.

Completion time includes agent-directed retrieval, processing, plotting and API calls. Setup is recorded separately; source-version checks are outside solve time. Per-skill execution times distinguish fetches from transformations in skills traces. Proxy records include encrypted bytes transferred and connection durations for both arms; connection durations overlap and must not be summed or described as exact download time. Static basemap preinstallation is equal in both conditions; source/proxy/OS network latency can still vary.

## Model experiment

`configs/end-to-end-v1.json` prespecifies five models (Fable, Astra, DeepSeek, Gemini Flash-Lite and Qwen 9B), three tasks, two conditions, and one repetition: **30 attempts**, with a $15 reported-spend stop threshold. This is a separate experiment, with new images, prompts and limits; do not pool it with the diagnostic study. It covers frontier, large open-weight, economy, and smaller open-weight models. The original Sonnet results remain in the diagnostic comparison; the new panel uses two frontier models to limit redundant premium-model spend.

The suite is small and deliberately chosen. Success rates and paired tests are descriptive and exploratory; three cases cannot support broad rankings or a claim of statistical equivalence. Provider errors, source errors, invalid model actions, catalog failures, wrong answers, and missing figures remain distinguishable in traces.

## Commands

```bash
# Offline reproduction of the oracle from checked-in raw provider bytes
.venv/bin/python references/e2e/oracle.py

# Build separate images, then validate both reference routes with real downloads
.venv/bin/python -m weather_bench.cli build-e2e-images
.venv/bin/python -m weather_bench.cli validate-end-to-end

# Independent, isolated model study and dashboard export
.venv/bin/python -m weather_bench.cli study --config configs/end-to-end-v1.json
.venv/bin/python -m weather_bench.cli export
```

Validation writes `results/e2e-reference.json`; public case briefs are in `cases/e2e-*.json`. Reference figures are in `docs/artifacts/reference/`. The dashboard task drawers expose source notes, expected answers and reference figures; run drawers expose model traces, submitted figures and network evidence. `results/e2e-queue.json` records the model study's queued/running/completed state when launched through the queue worker.

## Pilot recovery and scoring sensitivity

The original end-to-end worker terminated after 16 saved attempts. Its queue file
incorrectly remained `running`. Seven returned responses from the next Qwen heat
attempt were recovered from raw journals, together with the execution feedback
visible in those requests. That attempt is retained as **interrupted and unscored**;
unknown timing fields are null, and its $0.0047994705 known charge plus a reserve
for a possible in-flight request are retained. The remaining untouched cells
resume in `20260929T213240Z-167f76`; substantive attempts are not rerun.
Workers now publish a five-second heartbeat and write turn checkpoints. The
static dashboard refreshes every 15 seconds and labels stale worker snapshots.

A post-hoc audit found a task-contract ambiguity affecting the two rainfall cases.
The registered oracle and catalog fetcher clip negative daily precipitation
increments to zero. The original briefs do not specify this clipping rule.
Direct differences between cumulative endpoints are therefore also consistent
with the brief. Fable's two Python rainfall submissions pass an independent
endpoint-difference oracle (including figure delivery), although they fail the
registered oracle by up to approximately 0.0021 mm. This is **not evidence of a
meaningful weather-forecasting error**. The final audit also identifies Astra’s
Python revision submission as passing the endpoint-difference oracle, for three
additional submissions passing this alternative check.

`results/rainfall-semantics-audit.json` records that sensitivity check for all
saved rainfall attempts in both arms. It does not alter the original answers,
scores, prompts or model traces. The dashboard marks this cohort provisional and
exposes the alternative check in each audited run. A future confirmatory cohort
must state preprocessing semantics in the shared task brief before any model runs;
its outcomes must remain separate from this pilot. Provider failures and this
ambiguity prevent using the current cohort as a defensible model ranking.

Dashboard comparisons default to task outcomes, excluding provider errors and
unscored attempts. “All scored attempts” retains provider failures in operational
success and resource averages. All costs, including failures, remain in reported
spend and per-run traces. Neither view pools the synthetic and real-data cohorts.

## Independent provider recovery cohort

`configs/end-to-end-recovery-v2.json` registers 30 new attempts before execution. It retains the five model IDs, three tasks, both conditions, scientific answers and limits. Both conditions now receive explicit JSON output mode, the same bounded retry policy, and the rainfall daily-increment clipping rule. Results remain separate from the original pilot; this is not a controlled estimate of any single infrastructure change.

Small live probes passed for the selected routes. Replaying two original Gemini failures reproduced `MALFORMED_FUNCTION_CALL` without JSON mode; both passed with JSON mode, including on the original provider. Reports are in `results/provider-recovery-probes.json`, `results/provider-confirmation-probes.json`, and `results/gemini-response-replays.json`. Direct DeepSeek was rejected by the account's existing privacy policy and is excluded; that policy was not changed.

DeepSeek uses Wafer then Novita; Qwen uses Parasail then DeepInfra; Gemini uses AI Studio then Vertex global. Fable and Astra keep their tested original providers. Fallback stays within the same model and explicit provider allowlist, with route price caps. Actual returned provider and usage remain in each trace.

Transient HTTP 429/500/502/503/504 responses can retry at most three times per attempt, at most twice consecutively, respecting Retry-After up to a 30-second wait and the task deadline. Authentication, validation errors and ambiguous transport timeouts are not retried. Retries consume the original 40-request allowance; earlier agent actions are never reexecuted automatically. Retry waits count in solve time and all reported charges count toward spend. Unconfirmed charges remain marked unknown and receive a conservative reserve under the $15 study stop threshold. Malformed model responses receive error feedback within the normal request budget without executing their visible action.

## Ministral 3B model addition

`configs/end-to-end-ministral-v2.json` registers six further attempts: Ministral 3 3B on all three real-forecast cases in both conditions. It queues after the recovery batch to avoid concurrent evaluation workloads affecting timing. All per-attempt limits, prompts, preprocessing, grading and retry rules match `end-to-end-v2`. The additional batch has a $1 reported-spend stop threshold. Ministral does not support the optional reasoning-effort parameter; the runner omits unsupported parameters consistently.

The checked route is `mistral/zdr`, with input/output price caps of $0.10 per million tokens. `results/ministral-provider-probes.json` retains all compatibility responses. Both conditions returned valid JSON actions. The skills probe followed the exact requested actions; the No Skills response generated unrelated code instead of the requested arithmetic check. This is retained as an instruction-following mismatch, not silently treated as a passing probe or a service failure. No returned probe code was executed.

The six-model dashboard comparison links the two batches explicitly and validates matching task definitions, per-attempt budgets, protocol settings and catalog revision. Existing models and attempts cannot be replaced or duplicated by an extension. Statistics are recomputed over the six-model panel, including multiple-comparison adjustment. Individual batches remain selectable, and each combined-view run identifies its source batch. Adding a model after seeing earlier results remains exploratory; neither small parameter count nor an endpoint check establishes how well it will perform on forecasting tasks.

The extension has separate queue, summary, audit and findings files (`results/ministral-queue.json`, `results/ministral-summary.json`, `results/ministral-audit.json`, `MINISTRAL_FINDINGS.md`). The queue automatically refreshes the dashboard, builds the portable HTML and audits the recorded attempts.
