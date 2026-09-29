# Experiment design

## Question and hypotheses

Does access to the weather skill catalog improve scientific task success or reduce tokens, billed cost, and completion time compared with the same agent using scientific Python alone? These are hypotheses to measure, not assumed outcomes. Skills may cost more tokens or time when discovery and CLI retries outweigh their benefit.

The experimental unit is one `(model, case, condition, repetition)` run. Each run gets a fresh conversation and workspace. Pair conditions by model, case, and repetition; randomize their execution order with a recorded seed. The current runner executes runs sequentially to avoid concurrent API demand and host load confounding latency.

## Conditions

| Condition | Python | Catalog docs | Actual skill calls | Execution feedback |
|---|---|---|---|---|
| `skills` | Yes | On demand, with a name/description discovery index | Yes | Yes |
| `python` | Yes | No | No | Yes |
| `python_one_shot` | One generated program | No | No | No |
| `docs_only` (optional) | Yes | On demand | No | Yes |

The main two conditions have equal maximum model calls, total code/skill executions, output tokens per request, cumulative tokens, context bytes, task time, execution time, CPU, and memory. These are ceilings, not equal actual resource consumption. Documentation reads consume a model turn and prompt tokens but no execution slot. The one-shot condition intentionally changes feedback and retry availability and must not be used to attribute all differences to skills.

The Python environment is the same across conditions and includes NumPy, pandas, xarray, SciPy, cftime, pint, and xarray-regrid. The skill service adds the pinned core and catalog scripts. Thus the experiment measures reusable expert guidance and implementation, not exclusive access to a numerical library. All conditions receive the same task metadata, including dimensions, variable attributes, and coordinate labels. Values are read from identical input files. No condition is shown the answer key or reference recipe.

A provider-neutral action protocol supports JSON actions and a single fenced Python program. Minor JSON newline formatting is tolerated. This avoids requiring a particular vendor's native function-calling API. Actual Python execution, rather than a prose answer, is available in every condition. The model must save `answer.json`. The reported pilot uses one action per response. Optional batched actions are available for future experiments: a model can plan several sequential actions in one response, the host traces each child and stops on error, and execution budgets still count every child. `python_one_shot` remains one program with no feedback. Batching changes the protocol and must be studied separately from the existing pilot.

## Tasks and ground truth

The first ten tasks are synthetic diagnostic fixtures focused on transformation and composition. They deliberately stress errors that can change a scientific conclusion:

1. Regional rainfall: clip bounds, weekly rate aggregation, incomplete periods, cosine latitude weighting.
2. Ensemble flux spread: water-density conversion, member-wise weekly totals, sample standard deviation.
3. Legacy accumulations: difference amounts before weekly aggregation and ensemble median.
4. Forecast bias: valid-date conversion, Kelvin offset, naming, date intersection, temporal mean.
5. IOD: build a climatology, subtract before spatial weighting, use the two correct dipole boxes.
6. Model disagreement: select a matching lead, normalize units, concatenate, sample spread.
7. Rolling rainfall: select disjoint windows before rate-to-total conversion.
8. Calendar alignment: noleap versus Gregorian, preserve dates and exclude the unmatched leap day.
9. Spatial alignment: interpolate onto the reference grid before differencing.
10. Irregular precipitation: integrate duration-weighted rates from CF bounds.

Oracles use direct NumPy/stdlib arithmetic and do not call catalog functions. Each is cross-checked by an actual pinned catalog pipeline, including execution in the production Docker environment. Dates, keys, units, and array shapes match exactly. All numerical values must be finite and within `abs_tol=1e-6` or `rel_tol=1e-6` using `math.isclose`. Boolean-as-number and NaN/Infinity answers are rejected. These tolerances account for numerical implementations; they do not use an LLM judge. Identical answers always receive the same verdict.

Input archives have fixed Zip metadata and per-store SHA-256 hashes. No live download, current date, geocoding, unpublished data, or provider credentials enter a graded case. This makes the ground truth reproducible without access to external weather services. It also limits the scope of the conclusions: this suite does not measure live source discovery, retrieval, map aesthetics, or operational forecast skill.

## Workflow measurement

The host records every document read, Python execution, and skill invocation, with arguments, duration, exit code, and errors. Python never sees the skill code: calls are brokered into a separate container sharing only the current task's files. Failed calls remain visible. Skill logs cannot be forged by writing a claimed history inside `answer.json`.

Process conformance is a separate binary score. It requires distinct successful calls matching reference nodes and important argument values, with upstream artifacts feeding downstream calls. Only required dependency edges are ordered; independent branches can be interleaved. Attempts to deaccumulate already-rate inputs are flagged. This is deliberately stricter than numerical correctness: index selection instead of coordinate selection, different equivalent period spellings, Python substitutions, or alternative valid algorithms can pass the answer check and miss recipe conformance. It is not proof that the final JSON was derived from those artifacts, and is not used to declare a numerical failure. Future versions can add validated equivalence classes without rewriting older scores.

## Isolation and reproducibility

Each run has fresh `/inputs` (read-only) and `/work` mounts, a new conversation, and new containers. No repository root, answer module, previous output, API key, Docker socket, or host home directory is mounted. Containers use a read-only root, no network, no Linux capabilities, no-new-privileges, non-root UID, one CPU, 1 GB RAM, a PID cap, and bounded execution time. A timed-out exec kills its container rather than leaving code running. Output is read through the container to avoid following agent-created symlinks on the host.

The host alone sends requests to OpenRouter. Provider routes are fixed per model and model fallback is disabled. Exact returned model/provider names, request IDs, usage, finish reasons, catalog/core commits, dependency pins, code hash, fixture hashes, and image IDs are recorded. Image setup and dependency installation happen before measured inference; per-run container startup is tracked separately from solve time.

Model generations are not guaranteed deterministic: sampling, routing infrastructure, and provider kernels can vary. Provider-side prompt caching is also not eliminated by a fresh local workspace; cache-read tokens are recorded and reported separately. Repetitions are necessary. The deterministic guarantee applies to inputs, expected answers, and grading, not to LLM behavior or service latency.

## Measurements and reporting

- **Task success:** all required numerical and structural checks pass. Every attempted run stays in the denominator. Infrastructure errors and budget stops have explicit statuses.
- **Workflow conformance:** reference nodes and artifact dependency edges pass, separately from success.
- **Tokens:** sum prompt and completion tokens over every request. Reasoning and cache-read tokens are recorded as subsets, not added again to the total.
- **Cost:** sum `usage.cost` reported by OpenRouter. Missing cost is unknown, never free; the study stops on unknown accounting. Cost per success includes spend on failed attempts.
- **Latency:** wall time, container setup, solve loop, API time, and execution time; show median and p90. Timed-out and unsuccessful attempts remain in resource metrics.
- **Paired effects:** within a selected experiment, compare shared `(case, repetition)` attempts for each model. Show success percentage-point difference and skills/Python time, token, and cost ratios. Pairs containing a provider error on either side are excluded from capability comparisons; those failures remain in the operational attempt table. Do not pool unequal task coverage or conflate pilot experiments with changed harness versions.

The pilot is one repetition on three cases. It is descriptive, with raw denominators, and has no significance claim. For a briefing-grade study, run all ten cases and at least three repetitions, expand task families and fixture variants, include `docs_only`, and add task-clustered bootstrap intervals. A larger sample of repeated runs on the same three fixtures alone does not establish generalization. Public fixtures may eventually enter training corpora; maintain private variants for later held-out evaluation.

## Accounting sources

The runner follows OpenRouter's [usage accounting documentation](https://openrouter.ai/docs/cookbook/administration/usage-accounting): usage is returned automatically, and `usage.cost` is the amount charged. It snapshots the [model catalog](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties) at study start. Price-derived estimates are not substituted for billed cost.

## Pilot infrastructure recovery

The first provider route for DeepSeek returned 429 errors, including errors nested inside HTTP-200 completion objects. A recovery run retains every completed non-DeepSeek result and reschedules **all** DeepSeek conditions on one verified route before any DeepSeek agent action. Original transport failures remain archived and are not silently converted to model reasoning failures. This is a provider recovery, not selective rerunning of wrong numerical answers.

Two operator interruptions during infrastructure repair left one Gemini and one DeepSeek request without returned generation IDs. Completed charges from interrupted attempts are recorded separately; their final in-flight charges are explicitly unknown. A cumulative $0.20 reserve protects the study stop threshold and is not reported as actual billed cost. The final completed pilot excludes DeepSeek as a whole after repeated provider failures on two routes. Its partial outcomes, including a numerical failure, remain in earlier records. The completed comparison contains 27 attempts across the other three models.

The configured cumulative token limit is checked between requests and can be crossed by one response. HTTP read timeouts are inactivity limits; a provider that sends keepalive traffic can exceed that duration. Recorded wall time is therefore the measurement to use for the pilot's UX comparison, not a claim that every request met a hard total deadline.

## Publication boundary

The dashboard export uses an allowlist. It includes task briefs, reference answers, numeric run metrics, stop reasons, provider names, and action/argument sequences. The user-requested run log export also includes executed Python, recorded stdout/stderr, visible model responses, agent system instructions, and per-request usage. It excludes hidden reasoning text, raw API envelopes, request headers, credentials, and account identifiers; credential-shaped text and host user paths are redacted. The runner bounds stdout at 16,000 characters and stderr at the last 8,000 characters, so these are the recorded logs rather than unlimited process transcripts. Model calls and execution events remain separate ordered sequences; historical event-to-call timing is not invented. Archived records without detailed logs are explicitly marked unavailable. Reference answers are public for human auditing, but the isolated evaluation runtime cannot access the dashboard or repository. GitHub Pages deployment is a manual workflow, not an automatic side effect of running experiments.

## Skills-only v2: expanded operational comparison

`configs/expanded-v2.json` specifies 120 attempts: Fable 5.1, GPT-6 Astra, Sonnet 5.5, Gemini 3.1 Flash-Lite, DeepSeek V4.1 Flash, and Qwen3.5 9B; all ten tasks; skills-only and iterative Python; one repetition. Provider routes passed an independent protocol preflight. DeepSeek uses Fireworks because its direct route conflicted with the account's existing data policy. Preflight billing is recorded separately in `results/preflight-v2.json`.

The new `skills_only` condition requires reading each invoked guide in an earlier model response. The host rejects Python actions, including Python nested in a batch, and its sandbox has no general Python execution service. The agent can invoke only allowlisted catalog scripts. It submits a declarative mapping from output artifacts to answer fields; a fixed, case-independent serializer reads values and formats dates/timedeltas. It cannot calculate, select, aggregate, evaluate code or reference inputs as computed outputs. The host checks that referenced stores came from successful skill calls. All ten reference tasks pass through this exact mechanism (`results/skills-only-validation.json`).

The system prompt includes three catalog-wide compatibility notes documented before model evaluation: use the working standard-unit conversion path, pass concat inputs as one list, and preserve time bounds during aggregation. These are disclosed runtime errata, not case-specific recipes or answer values. The catalog and numerical grading remain unchanged.

Both new conditions allow sequential batching, retries, 24 model responses, 24 executions, 250,000 cumulative tokens, 8,192 output tokens per response, and the same time limits. The skills agent receives the catalog guidance and the Python agent receives the scientific Python environment. This is a comparison of two deployable agent configurations; it no longer isolates the marginal effect of adding skills while keeping code execution available in both arms. The baseline approximates an iterative coding-agent workflow, not the complete Codex or Claude Code product. One-shot is absent from the new study and from the primary leaderboard; its historic runs remain archived.

The new study is separately versioned and must not be pooled with the original availability-only pilot. See [STATISTICS.md](STATISTICS.md) for Wilson intervals, exact paired McNemar tests, multiplicity adjustment, and limits from the small diagnostic suite.

### Transport repair during the expanded study

The first ten attempts are preserved in `20260929T184130Z-9023ed`. Its tenth attempt was interrupted after provider keepalive traffic bypassed the HTTP inactivity timeout. The resumed study retains all ten attempts, including the interruption; it does not rerun failures. Subsequent requests have a total wall-clock deadline. Failed request duration is included in recorded model time. Partial batch feedback is retained if a later action in that batch is invalid. Prompts, model routes, task data, scientific operations and answer grading are unchanged; both code revisions are recorded.

Unconfirmed requests remain explicitly unknown in cost metrics. A conservative reserve based on message bytes, maximum output length and fixed endpoint prices protects the $25 stop threshold; it is not reported as billed cost. The stop threshold is checked between requests and is not a provider-enforced hard spending cap. Provider errors remain in operational results and resource measurements, but their matched pairs are excluded from the exploratory capability test. Operator-interrupted attempts remain in the logs and recorded spend but are unscored and excluded from model success/resource averages. The inherited interruption retains its original elapsed time.

The first two Sonnet requests exposed a separate configuration error: model-level capability metadata included temperature, while the pinned Anthropic endpoint did not support it. Endpoint-specific parameter selection now omits temperature for this route. All six routes subsequently passed preflight with the exact scored-request parameters (`results/preflight-v2.json`). Those two rejections occurred before any response or agent action and remain archived as infrastructure; the untouched Sonnet tasks are scheduled again. A Fable request interrupted before its first response during this repair is treated the same way. Substantive attempts, including the earlier Qwen interruption, are retained without rerunning them. The resumption records the full code-revision history.

The reporting layer labels a `ReadTimeout` at or beyond the shared task deadline as `task_timeout`; its raw transport status is preserved as `original_status`. Such a run exhausted the agent's task budget and is not removed from the paired analysis as a provider-only failure. Earlier request timeouts remain provider errors. This changes stop-reason classification, not saved answers or numerical grading.

### Agent-interface scope

The runner uses text JSON actions, not vendor-native function calling or the complete Codex/Claude Code clients. Malformed actions, wrong action names and extra wrappers can consume retries before any scientific code executes. Report those observed protocol failures separately from wrong numerical answers. Results measure this explicit agent loop and its tool interfaces; they do not establish how the same models would perform in a different production agent framework. A native-tool or more tolerant adapter is a distinct experimental factor for a subsequent, separately versioned comparison.

The client does not request explicit prompt-cache breakpoints. Any provider-applied caching is recorded through returned usage; cached input is still included in total tokens and actual billing remains the cost measure. A production client that configures caching differently can have different costs, especially for long skill guides repeated in conversation history. The equal maximum budgets do not imply equal prompt length or equal numbers of model round trips.
