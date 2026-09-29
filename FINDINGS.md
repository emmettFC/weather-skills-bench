# Initial pilot: findings and limits

The completed pilot contains **27 attempts**: three models, three cases, three conditions, one repetition. Cases cover complete regional rainfall weeks, legacy cumulative rainfall, and forecast-versus-observation temperature bias. The full benchmark has ten validated cases.

| Model | With skills | Iterative Python | One-shot Python |
|---|---:|---:|---:|
| Claude Sonnet 4.6 | 3/3 | 3/3 | 2/3 |
| Gemini 2.5 Flash | 1/3 | 2/3 | 1/3 |
| Qwen3 30B A3B | 0/3* | 1/3 | 1/3 |

*Two Qwen skills attempts ended in provider errors. These are included in the operational attempt count but excluded from matched capability comparisons. They are not evidence that Qwen cannot solve those tasks with skills.

The scored attempts cost **$0.4127602644** according to returned OpenRouter usage. Diagnostic runs cost extra. Two operator-interrupted requests have unconfirmed final charges; the experiment notes and accounting artifact disclose this rather than claiming an exact all-in spend.

## What the data support

The pilot **does not establish token, latency, cost, or accuracy savings from skills**. For Sonnet, both main conditions solved all three tasks. With skills available, mean tokens were about 14,605 versus 4,349 for Python only; median solve time was 21.9 versus 10.5 seconds; total scored cost was $0.16744 versus $0.06278. These describe this small task set and this agent loop, not a general model or catalog ranking.

The one-shot comparison is a separate question about the combination of skill access and iteration. Its lower accuracy for Sonnet cannot be attributed solely to missing skills, since the feedback budget is also different.

All ten tasks are feasible in both environments: the actual catalog reference pipelines and independent, one-program Python solutions both pass in isolated containers. Model failures are therefore not caused by impossible task contracts. Catalog compatibility issues are nevertheless present and documented in [CATALOG_REVIEW.md](CATALOG_REVIEW.md).

## Operational observations

- The catalog discovery index and repeated context contribute to token overhead. Models also sometimes guess CLI flags, retry commands, or use Python instead of the available skills. The trace records the behavior rather than assuming skill use.
- The pilot protocol executes one action per model response. That round-trip cost is part of the measured agent implementation and should not be mistaken for an intrinsic limit of the skill scripts.
- Optional batched actions are implemented and unit-tested for the next study (`configs/full-batched.json`). They preserve each individual invocation, order, and execution count, and stop at the first error. They were **not used** to generate or retroactively improve the reported pilot.
- DeepSeek V3.2 encountered repeated provider errors on two routes. Its partial results, including a completed but incorrect one-shot answer, remain visible in earlier experiment records. It was removed as a whole from the completed three-model comparison; individual wrong answers were not selectively rerun.
- Two requests were interrupted during infrastructure repair. Known diagnostic charges and unknown final charges are recorded separately from the scored-run cost.

## Before briefing a catalog-wide benefit

Run all ten cases with repeated trials, include `docs_only`, and compare the serialized and batched protocols in separate experiments. Add realistic retrieval cases using frozen upstream responses and the actual fetchers, plus private fixture variants. Use task-clustered uncertainty intervals and stable provider capacity. The current public synthetic transformation suite is a diagnostic development benchmark, not proof of broad operational value.

## Trace audit: why the skills-available condition underperformed

Audited the completed pilot `20260929T171136Z-6d77a9` on 2026-09-29. The dashboard now calls this condition **Skills available**. The original prompt exposes guides and scripts but does not require the agent to use them or read a guide first.

- **Zero of the nine skills-available runs read a `SKILL.md`.** Only the three Gemini runs called any skill. None matched the full reference workflow. This pilot does not measure consistent, properly instructed skill use.
- **Sonnet called no skills in any of its three skills-available runs.** It solved all three through Python, versus 3/3 in iterative Python. Across the three cases it made 12 model requests versus 8, with four protocol errors versus two. Its initial system prompt was 8,134 characters in the skills condition; the first request used roughly 2,551–2,766 input tokens versus 755–970 without skills. Mean total tokens were 3.36× and billed cost 2.67× the Python comparator. More context and requests are observed; this is not evidence that executing a skill is 2.67× more expensive.
- **Gemini's rainfall run guessed interfaces rather than reading the guide.** It tried `--north/--west/...`, then comma-separated bboxes where the guide specifies `N/W/S/E`, then unsupported selection and aggregation flags. Seven of its 16 skill executions failed. It exhausted its execution budget without an answer; iterative Python passed this case. Run: `40659f11235a45f099c3cb0a0b7b7768`.
- **Gemini's forecast-bias run hit a real catalog defect.** `unit-convert --to-units degree_Celsius` repeatedly failed with “no units attr,” despite inspection showing units. This is the pinned core/CLI interaction already documented in `CATALOG_REVIEW.md`. It also guessed rename and difference flags and exhausted its execution budget. Both main conditions failed this case, so the defect is evidence of wasted work, not proof of a paired accuracy loss on this case. Run: `4f585222f14147189a5bb9cebbfe0495`.
- **Qwen provides little usable evidence of a skill effect.** It called no skills; two skills-available attempts ended in upstream 429 errors. On forecast bias, both iterative arms repeatedly produced a scalar-indexing error. Availability, error recovery and scientific reasoning are distinct failure modes.
- **The benchmark currently rewards familiar short numerical programs.** Both arms receive input metadata and scientific Python libraries. The fixtures are small and the mathematical conventions explicit. On these tasks, writing one correct array operation can be simpler than discovering and composing several CLIs. That can be a legitimate negative result; it does not establish performance on retrieval, larger datasets, operational provenance or ambiguous source conventions.

The reference pipelines prove feasibility, but were authored with knowledge of the catalog's supported paths. They do not prove discoverability from its current guides. The single-action JSON interface also creates protocol overhead: some Sonnet responses contained a fenced program followed by a second submit action and were rejected. This affects both main conditions and is part of this harness, not an intrinsic catalog property.

These are trace-backed explanations and plausible contributing mechanisms, not a randomized causal decomposition of prompt size, catalog defects, model settings and tool design. The next version should test those factors explicitly; see [MODEL_REVIEW.md](MODEL_REVIEW.md). Preserve this pilot rather than changing its scores or selectively rerunning failures.
