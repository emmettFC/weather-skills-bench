# Small-model comparison

**Complete: 40/40 recorded attempts.** Study `20260929T214800Z-fd1ee0`.

2 models, 10 fixed diagnostic tasks, skills-only versus No Skills (Python with execution feedback), one repetition. One-shot is absent. Operator interruptions are unscored; provider errors remain in operational success rates. Matched capability tests exclude provider errors and interruptions.

| Model | Condition | Passed / scored | Median seconds | Mean tokens | USD / attempt | USD / success | Provider errors |
|---|---|---:|---:|---:|---:|---:|---:|
| Llama 3.2 1B | No Skills | 0/10 | 178.4 | 65,796 | Unknown | — | 8 |
| Llama 3.2 1B | Skills only | 0/10 | 17.9 | 77,905 | $0.0023 | — | 0 |
| Llama 3.2 3B | No Skills | 0/10 | 38.1 | 110,112 | $0.0077 | — | 1 |
| Llama 3.2 3B | Skills only | 0/10 | 14.7 | 192,855 | $0.0123 | — | 0 |

Reported study charges: **$0.2591**. Unconfirmed charges are additional; the $0.1243 reserve is a budget precaution, not billed spend. Preflight charges are recorded separately in `results/preflight-small-models.json`.

## Paired comparisons

| Model | Evaluable pairs | Skills wins | No Skills wins | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Llama 3.2 1B | 2 | 0 | 0 | 1.0000 | 1.0000 |
| Llama 3.2 3B | 9 | 0 | 0 | 1.0000 | 1.0000 |

These are exploratory comparisons on a small, deliberately chosen synthetic task set. An insignificant difference does not establish equivalence. Interim rows have unequal coverage and should not be used to rank models.

## Interpretation boundaries

- Scientific calculations, output-contract failures, action-format rejections, and provider failures are different phenomena. Inspect the linked run traces before attributing a failed task to weather reasoning.
- The skills-only host requires earlier guide reads and catalog calls, blocks model-written Python, and serializes answers from produced artifacts. Early failures can occur before any skill is executed.
- The Python comparator can inspect inputs, execute programs, receive errors, and retry. The JSON-action harness approximates that workflow; it does not run the complete Codex or Claude Code clients.
- Reading long guides, repeated context, CLI discovery and extra calls can increase resource use. Provider-applied caching is recorded, but explicit cache breakpoints are not requested.
- This study does not establish operational forecast quality in Africa, local-hosting feasibility, or performance on African networks. See [model review](MODEL_REVIEW.md), [methodology](METHODOLOGY.md), and [statistics](STATISTICS.md).

The original availability-only pilot and its explanation remain in [FINDINGS.md](FINDINGS.md). The [dashboard](docs/index.html) contains task briefs, exact answers, clickable comparisons, and per-run traces.
