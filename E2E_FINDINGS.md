# End-to-end real-forecast study

**Provisional:** Two rainfall briefs omit the negative-increment clipping rule used by the reference. A separate sensitivity audit checks direct cumulative differences without changing registered scores. Provider failures and this ambiguity prevent a defensible model ranking.

See END_TO_END.md and results/rainfall-semantics-audit.json for the independent sensitivity check. Registered scores are unchanged.

**Complete: 30/30 recorded attempts.** Study `20260929T213240Z-167f76`.

5 models, 3 real-forecast end-to-end tasks, skills-only versus iterative Python, one repetition. One-shot is absent. Operator interruptions are unscored; provider errors remain in operational success rates. Matched capability tests exclude provider errors and interruptions.

| Model | Condition | Passed / scored | Median seconds | Mean tokens | USD / attempt | USD / success | Provider errors |
|---|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | Iterative Python | 1/3 | 65.5 | 37,654 | $0.4800 | $1.4400 | 0 |
| Claude Fable 5.1 | Skills only | 2/3 | 74.6 | 77,959 | $0.8696 | $1.3043 | 1 |
| DeepSeek V4.1 Flash | Iterative Python | 0/3 | 47.2 | 140,464 | $0.0232 | — | 2 |
| DeepSeek V4.1 Flash | Skills only | 0/3 | 257.2 | 312,727 | $0.0323 | — | 1 |
| Gemini 3.1 Flash-Lite | Iterative Python | 0/3 | 4.3 | 0 | $0.0000 | — | 3 |
| Gemini 3.1 Flash-Lite | Skills only | 0/3 | 13.0 | 11,412 | $0.0043 | — | 3 |
| GPT-6 Astra | Iterative Python | 0/3 | 52.9 | 31,639 | $0.2390 | — | 0 |
| GPT-6 Astra | Skills only | 3/3 | 56.0 | 103,376 | $0.3727 | $0.3727 | 0 |
| Qwen3.5 9B | Iterative Python | 0/3 | 57.1 | 2,182 | $0.0002 | — | 3 |
| Qwen3.5 9B | Skills only | 0/2 | 0.5 | 0 | $0.0000 | — | 2 |

Reported study charges: **$6.0688**. Unconfirmed charges are additional; the $0.0573 reserve is a budget precaution, not billed spend. Preflight charges are recorded separately in `results/preflight-v2.json`.

## Paired comparisons

| Model | Evaluable pairs | Skills-only wins | Python-only wins | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | 2 | 2 | 0 | 0.5000 | 1.0000 |
| DeepSeek V4.1 Flash | 1 | 0 | 0 | 1.0000 | 1.0000 |
| GPT-6 Astra | 3 | 3 | 0 | 0.2500 | 1.0000 |

These are exploratory comparisons on a small, deliberately chosen archived real-forecast task set. An insignificant difference does not establish equivalence. Interim rows have unequal coverage and should not be used to rank models.

## Interpretation boundaries

- Scientific calculations, output-contract failures, action-format rejections, and provider failures are different phenomena. Inspect the linked run traces before attributing a failed task to weather reasoning.
- The skills-only host requires earlier guide reads and catalog calls, blocks model-written Python, and serializes answers from produced artifacts. Early failures can occur before any skill is executed.
- The Python comparator can inspect inputs, execute programs, receive errors, and retry. The JSON-action harness approximates that workflow; it does not run the complete Codex or Claude Code clients.
- Reading long guides, repeated context, CLI discovery and extra calls can increase resource use. Provider-applied caching is recorded, but explicit cache breakpoints are not requested.
- This study does not establish operational forecast quality in Africa, local-hosting feasibility, or performance on African networks. See [model review](MODEL_REVIEW.md), [methodology](METHODOLOGY.md), and [statistics](STATISTICS.md).

The original availability-only pilot and its explanation remain in [FINDINGS.md](FINDINGS.md). The [dashboard](docs/index.html) contains task briefs, exact answers, clickable comparisons, and per-run traces.

Live forecast retrieval and plotting are included in completion time. Source versions are checked before and after each attempt. Heat task has a documented catalog reference defect; a correct alternative remains eligible. See END_TO_END.md.
