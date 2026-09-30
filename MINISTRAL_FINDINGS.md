# End-to-end real-forecast study

**Complete: 6/6 recorded attempts.** Study `20260930T050605Z-3ebbaf`.

1 models, 3 real-forecast end-to-end tasks, skills-only versus No Skills (Python with execution feedback), one repetition. One-shot is absent. Operator interruptions are unscored; provider errors remain in operational success rates. Matched capability tests exclude provider errors and interruptions.

| Model | Condition | Passed / scored | Median seconds | Mean tokens | USD / attempt | USD / success | Provider errors |
|---|---|---:|---:|---:|---:|---:|---:|
| Ministral 3 3B | No Skills | 0/3 | 29.9 | 23,458 | Unknown | — | 2 |
| Ministral 3 3B | Skills only | 0/3 | 36.1 | 297,095 | Unknown | — | 3 |

Reported study charges: **$0.0169**. Unconfirmed charges are additional; the $0.0966 reserve is a budget precaution, not billed spend. Preflight charges are recorded separately in `results/ministral-provider-probes.json`.

## Paired comparisons

| Model | Evaluable pairs | Skills wins | No Skills wins | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|

These are exploratory comparisons on a small, deliberately chosen archived real-forecast task set. An insignificant difference does not establish equivalence. Interim rows have unequal coverage and should not be used to rank models.

## Interpretation boundaries

- Scientific calculations, output-contract failures, action-format rejections, and provider failures are different phenomena. Inspect the linked run traces before attributing a failed task to weather reasoning.
- The skills-only host requires earlier guide reads and catalog calls, blocks model-written Python, and serializes answers from produced artifacts. Early failures can occur before any skill is executed.
- The Python comparator can inspect inputs, execute programs, receive errors, and retry. The JSON-action harness approximates that workflow; it does not run the complete Codex or Claude Code clients.
- Reading long guides, repeated context, CLI discovery and extra calls can increase resource use. Provider-applied caching is recorded, but explicit cache breakpoints are not requested.
- This study does not establish operational forecast quality in Africa, local-hosting feasibility, or performance on African networks. See [model review](MODEL_REVIEW.md), [methodology](METHODOLOGY.md), and [statistics](STATISTICS.md).

The original availability-only pilot and its explanation remain in [FINDINGS.md](FINDINGS.md). The [dashboard](docs/index.html) contains task briefs, exact answers, clickable comparisons, and per-run traces.

Live forecast retrieval and plotting are included in completion time. Source versions are checked before and after each attempt. Heat task has a documented catalog reference defect; a correct alternative remains eligible. See END_TO_END.md.
