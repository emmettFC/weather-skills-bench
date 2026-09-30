# End-to-end real-forecast study

**Complete: 30/30 recorded attempts.** Study `20260930T013445Z-a569f5`.

5 models, 3 real-forecast end-to-end tasks, skills-only versus No Skills (Python with execution feedback), one repetition. One-shot is absent. Operator interruptions are unscored; provider errors remain in operational success rates. Matched capability tests exclude provider errors and interruptions.

| Model | Condition | Passed / scored | Median seconds | Mean tokens | USD / attempt | USD / success | Provider errors |
|---|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | No Skills | 2/3 | 43.1 | 17,856 | Unknown | Unknown | 1 |
| Claude Fable 5.1 | Skills only | 2/3 | 117.4 | 221,078 | $2.4593 | $3.6889 | 0 |
| DeepSeek V4.1 Flash | No Skills | 3/3 | 26.7 | 50,187 | $0.0041 | $0.0041 | 0 |
| DeepSeek V4.1 Flash | Skills only | 0/3 | 297.4 | 167,402 | Unknown | — | 2 |
| Gemini 3.1 Flash-Lite | No Skills | 2/3 | 25.7 | 33,738 | Unknown | Unknown | 1 |
| Gemini 3.1 Flash-Lite | Skills only | 1/3 | 150.0 | 275,645 | $0.0711 | $0.2134 | 0 |
| GPT-6 Astra | No Skills | 1/3 | 51.4 | 17,344 | Unknown | Unknown | 2 |
| GPT-6 Astra | Skills only | 3/3 | 100.5 | 103,241 | $0.3744 | $0.3744 | 0 |
| Qwen3.5 9B | No Skills | 0/3 | 360.3 | 167,301 | Unknown | — | 2 |
| Qwen3.5 9B | Skills only | 0/3 | 218.5 | 155,090 | Unknown | — | 2 |

Reported study charges: **$10.0006**. Unconfirmed charges are additional; the $4.0439 reserve is a budget precaution, not billed spend. Preflight charges are recorded separately in `results/preflight-v2.json`.

## Paired comparisons

| Model | Evaluable pairs | Skills wins | No Skills wins | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | 2 | 0 | 0 | 1.0000 | 1.0000 |
| DeepSeek V4.1 Flash | 1 | 0 | 1 | 1.0000 | 1.0000 |
| Gemini 3.1 Flash-Lite | 2 | 0 | 1 | 1.0000 | 1.0000 |
| GPT-6 Astra | 1 | 0 | 0 | 1.0000 | 1.0000 |

These are exploratory comparisons on a small, deliberately chosen archived real-forecast task set. An insignificant difference does not establish equivalence. Interim rows have unequal coverage and should not be used to rank models.

## Interpretation boundaries

- Scientific calculations, output-contract failures, action-format rejections, and provider failures are different phenomena. Inspect the linked run traces before attributing a failed task to weather reasoning.
- The skills-only host requires earlier guide reads and catalog calls, blocks model-written Python, and serializes answers from produced artifacts. Early failures can occur before any skill is executed.
- The Python comparator can inspect inputs, execute programs, receive errors, and retry. The JSON-action harness approximates that workflow; it does not run the complete Codex or Claude Code clients.
- Reading long guides, repeated context, CLI discovery and extra calls can increase resource use. Provider-applied caching is recorded, but explicit cache breakpoints are not requested.
- This study does not establish operational forecast quality in Africa, local-hosting feasibility, or performance on African networks. See [model review](MODEL_REVIEW.md), [methodology](METHODOLOGY.md), and [statistics](STATISTICS.md).

The original availability-only pilot and its explanation remain in [FINDINGS.md](FINDINGS.md). The [dashboard](docs/index.html) contains task briefs, exact answers, clickable comparisons, and per-run traces.

Live forecast retrieval and plotting are included in completion time. Source versions are checked before and after each attempt. Heat task has a documented catalog reference defect; a correct alternative remains eligible. See END_TO_END.md.
