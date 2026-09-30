# Expanded skills-only study

**Complete: 120/120 recorded attempts.** Study `20260929T191336Z-7d322b`.

6 models, 10 fixed diagnostic tasks, skills-only versus No Skills (Python with execution feedback), one repetition. One-shot is absent. Operator interruptions are unscored; provider errors remain in operational success rates. Matched capability tests exclude provider errors and interruptions.

| Model | Condition | Passed / scored | Median seconds | Mean tokens | USD / attempt | USD / success | Provider errors |
|---|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | No Skills | 10/10 | 14.0 | 3,724 | $0.0520 | $0.0520 | 1 |
| Claude Fable 5.1 | Skills only | 10/10 | 33.2 | 55,465 | $0.5842 | $0.5842 | 0 |
| Claude Sonnet 5.5 | No Skills | 10/10 | 7.6 | 6,213 | $0.0169 | $0.0169 | 0 |
| Claude Sonnet 5.5 | Skills only | 10/10 | 17.2 | 96,516 | $0.1986 | $0.1986 | 0 |
| DeepSeek V4.1 Flash | No Skills | 10/10 | 37.6 | 17,328 | $0.0046 | $0.0046 | 0 |
| DeepSeek V4.1 Flash | Skills only | 8/10 | 27.1 | 64,221 | $0.0048 | $0.0060 | 2 |
| Gemini 3.1 Flash-Lite | No Skills | 6/10 | 4.8 | 4,739 | $0.0027 | $0.0044 | 0 |
| Gemini 3.1 Flash-Lite | Skills only | 4/10 | 27.4 | 88,401 | $0.0282 | $0.0706 | 0 |
| GPT-6 Astra | No Skills | 9/10 | 11.7 | 3,954 | $0.0539 | $0.0599 | 0 |
| GPT-6 Astra | Skills only | 10/10 | 16.9 | 26,662 | $0.1366 | $0.1366 | 0 |
| Qwen3.5 9B | No Skills | 3/10 | 89.1 | 16,441 | Unknown | Unknown | 4 |
| Qwen3.5 9B | Skills only | 1/9 | 191.3 | 40,791 | Unknown | Unknown | 7 |

Reported study charges: **$10.8985**. Unconfirmed charges are additional; the $5.4855 reserve is a budget precaution, not billed spend. Preflight charges are recorded separately in `results/preflight-v2.json`.

## Paired comparisons

| Model | Evaluable pairs | Skills wins | No Skills wins | Exact McNemar p | Holm-adjusted p |
|---|---:|---:|---:|---:|---:|
| Claude Fable 5.1 | 9 | 0 | 0 | 1.0000 | 1.0000 |
| Claude Sonnet 5.5 | 10 | 0 | 0 | 1.0000 | 1.0000 |
| DeepSeek V4.1 Flash | 8 | 0 | 0 | 1.0000 | 1.0000 |
| Gemini 3.1 Flash-Lite | 10 | 2 | 4 | 0.6875 | 1.0000 |
| GPT-6 Astra | 10 | 1 | 0 | 1.0000 | 1.0000 |
| Qwen3.5 9B | 2 | 1 | 0 | 1.0000 | 1.0000 |

These are exploratory comparisons on a small, deliberately chosen synthetic task set. An insignificant difference does not establish equivalence. Interim rows have unequal coverage and should not be used to rank models.

## Interpretation boundaries

- Scientific calculations, output-contract failures, action-format rejections, and provider failures are different phenomena. Inspect the linked run traces before attributing a failed task to weather reasoning.
- The skills-only host requires earlier guide reads and catalog calls, blocks model-written Python, and serializes answers from produced artifacts. Early failures can occur before any skill is executed.
- The Python comparator can inspect inputs, execute programs, receive errors, and retry. The JSON-action harness approximates that workflow; it does not run the complete Codex or Claude Code clients.
- Reading long guides, repeated context, CLI discovery and extra calls can increase resource use. Provider-applied caching is recorded, but explicit cache breakpoints are not requested.
- This study does not establish operational forecast quality in Africa, local-hosting feasibility, or performance on African networks. See [model review](MODEL_REVIEW.md), [methodology](METHODOLOGY.md), and [statistics](STATISTICS.md).

The original availability-only pilot and its explanation remain in [FINDINGS.md](FINDINGS.md). The [dashboard](docs/index.html) contains task briefs, exact answers, clickable comparisons, and per-run traces.
