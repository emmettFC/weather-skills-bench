# Model selection for African weather-service workflows

Reviewed 2026-09-29. The original selection was reasonable for a cheap harness smoke test, but insufficiently justified as a deployment-oriented comparison. It included two closed-weight price tiers and two open-weight models; provider failures then removed DeepSeek from the completed study. None of these results establishes suitability for operational forecasting in Africa.

## What the LLM is being selected to do

The LLM orchestrates retrieval, transformations, verification, and presentation; it is not itself the numerical weather forecast model. Evaluate its ability to preserve rainfall units, accumulation periods, valid dates, ensemble semantics, geographic boundaries, missing-data rules, and provenance. General coding or tool-use scores are useful screening evidence, not African forecast validation.

The WMO's [Malawi AI forecasting pilot](https://public.wmo.int/media/news/wmo-supports-artificial-intelligence-forecasting-pilot-africa) emphasizes local operational capacity, local data and knowledge, and early warnings. Its [Hydromet Gap Report summary](https://wmo.int/news/media-centre/hydromet-gap-report-launch-collaboration-needed-ensure-early-warnings-all) identifies observational coverage, maintenance, and data-quality gaps. These support prioritizing robust data handling and workable deployment conditions, rather than choosing an LLM because its marketing mentions weather.

Africa is not one deployment environment. A national meteorological service with a reliable hosted service and a regional office with intermittent connectivity have different constraints. The next evaluation should distinguish:

- Hosted API quality, cost per successful task, p50/p95 completion time, and provider failure rates.
- Local or nationally hosted open weights, including full model memory, quantization, hardware, electricity, maintenance, and offline operation.
- Analyst-facing language support, tested with real users and translated task variants if that is part of the product. The current English numerical suite does not establish competence in French, Arabic, Swahili, or other languages.
- Accuracy of analyses based on sparse or incomplete observations, plus explicit provenance and uncertainty. A cheap but scientifically wrong answer is not a useful saving.

OpenRouter tests hosted behavior. Their latency and prices do not establish performance on African networks or the cost of self-hosting. Measure those separately at representative operating locations.

## Review of the pilot choices

| Pilot choice | Assessment | Decision |
|---|---|---|
| Claude Sonnet 4.6 | A credible coding/agent baseline, but not the current upper capability tier. The three correct skills-available runs used no skills. | Keep as a historical bridge, not the sole frontier representative. |
| Gemini 2.5 Flash | A defensible older budget baseline, but the current OpenRouter listing announces retirement on October 20, 2026. | Replace for the next sustained study. |
| Qwen3 30B A3B Instruct 2507 | Covers inexpensive open weights, but is neither a very small dense model nor the clearest current choice for agentic coding. Two of its three skills-available attempts had provider errors. | Keep historical results; add a genuinely smaller model and a more recent open-weight agent candidate. |
| DeepSeek V3.2 | Useful as another open-weight family; the observed provider failures do not establish poor model reasoning. | Re-enter only with a validated stable route, in a separate, complete comparison. |

Sources: [Anthropic's Sonnet 4.6 description](https://www.anthropic.com/news/claude-sonnet-4-6), [Gemini 2.5 Flash availability](https://openrouter.ai/google/gemini-2.5-flash), [Qwen Instruct listing](https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507), [DeepSeek V3.2 listing](https://openrouter.ai/deepseek/deepseek-v3.2). The run-specific judgments above come from the local pilot, not vendor claims.

## Earlier candidate panel (superseded by the expanded study below)

This is a candidate panel, not an assertion that these models are already validated for the application. No additional paid runs were made for this review.

| Role | Exact OpenRouter model ID | Weight access | Listed USD / 1M input / output tokens |
|---|---|---|---|
| Expensive capability reference | `anthropic/claude-opus-5.5` | Closed | $4 / $20 |
| Production-oriented capable reference | `anthropic/claude-sonnet-5.5` | Closed | $2 / $10 |
| Low-cost hosted baseline | `google/gemini-3.1-flash-lite` | Closed | $0.25 / $1.50 |
| Smaller local-deployment candidate | `qwen/qwen3.5-9b` | Open | $0.08 / $0.13 |
| Mid-size open-weight agent candidate | `qwen/qwen3.6-35b-a3b` | Open | $0.05 / $0.70 |

Prices are the displayed listings observed on the review date, not fixed-route quotes, measured task costs, or self-hosting estimates. Resolve and pin the provider before running; record returned billing. Cached input, reasoning, quantization and routing can change both cost and behavior. Opus 5.5 and Sonnet 5.5 are recent releases and need protocol/availability preflight before inclusion.

Sources: [Opus 5.5](https://openrouter.ai/anthropic/claude-opus-5.5), [Sonnet 5.5](https://openrouter.ai/anthropic/claude-sonnet-5.5), [Flash-Lite](https://openrouter.ai/google/gemini-3.1-flash-lite), [Qwen 9B](https://openrouter.ai/qwen/qwen3.5-9b), [Qwen 35B](https://openrouter.ai/qwen/qwen3.6-35b-a3b). Google's [Flash-Lite announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/) supports its intended low-cost, responsive role, but does not prove task accuracy here.

The [Qwen 35B model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) specifies **35B total / 3B active** parameters. The full weights still need storage and memory; “3B active” must not be presented as a 3B deployment footprint. The [9B model card](https://huggingface.co/Qwen/Qwen3.5-9B) makes it a more relevant smaller-model candidate, subject to measuring the complete multimodal model footprint and runtime overhead. Neither card proves adequate scientific accuracy.

As a targeted extension, test [Qwen3 Coder Next](https://openrouter.ai/qwen/qwen3-coder-next), an agentic coding model with 80B total / 3B active parameters, to separate coding specialization from model size. It is not a low-memory deployment baseline. The older [Qwen3 Coder 30B](https://openrouter.ai/qwen/qwen3-coder-30b-a3b-instruct) would have been a more targeted coding comparison than general Instruct, but its current listing announces retirement on October 8, 2026, so do not make a new long-lived experiment depend on it.

## Study changes needed before model ranking

1. Fix confirmed catalog defects, including the `unit-convert --to-units` path, and validate documented examples. Repin and rerun independent reference checks. Keep the current pilot intact.
2. Version the agent protocol. Compare **skills available** against **guided skill use** rather than silently treating availability as invocation. Guided use should instruct the agent to read applicable guides and use their supported operations; do not expose case-specific reference recipes or answers. Score answer correctness and process adherence separately.
3. Run the main Python comparator with the same iteration and execution budgets. Keep one-shot Python separate. Add `docs_only` to distinguish instruction value from reusable code.
4. Allow equivalent action batching in both main conditions. A single Python program can already perform several calculations; forcing a model round trip between every skill command creates avoidable serialization overhead. Report the new protocol separately.
5. Preflight provider capacity and action formatting. Fix the route and model settings within each paired comparison. A common `low` reasoning label is not an equal compute budget across model families; record actual reasoning tokens and also report per-model documented configurations. Avoid tuning on the graded fixtures.
6. Run all ten diagnostic tasks with repeated trials and new fixture variants, then add operationally representative tasks. Frozen CHIRPS/IMERG rain, forecast accumulations, local gauges, county/catchment boundaries, ensemble exceedance probabilities, missing-data thresholds, and onset/dry-spell definitions are useful candidates. Derive fixed independent answers and give both conditions equivalent source access.
7. Keep scientific correctness, skill adoption, workflow conformance, provider errors, token use, cost per success, and tail latency separate. Compare matched case coverage; do not pool old and new harnesses into a single leaderboard.

The existing rainfall fixture deliberately uses latitudes 0/30/60 to stress cosine weighting; it is a synthetic diagnostic, not an African operational case. More repetitions alone will not fix that external-validity gap. Operational forecast quality would additionally require historical verification against observations across regions, seasons and lead times, beyond this skill-execution benchmark.

## Expanded panel actually evaluated

The user's request for Fable, Astra and DeepSeek supersedes the earlier candidate list. `configs/expanded-v2.json` pins these six routes. All passed a short paid protocol preflight before the study; this verifies availability and response formatting, not scientific competence.

| Role | Model | Fixed provider | Input / output USD per million tokens |
|---|---|---|---|
| Frontier capability reference | Claude Fable 5.1 | Anthropic | $10 / $50 |
| Independent frontier family | GPT-6 Astra | OpenAI standard | $10 / $50 |
| Capable, lower-priced closed weights | Claude Sonnet 5.5 | Anthropic | $2 / $10 |
| Low-cost closed weights | Gemini 3.1 Flash-Lite | Google AI Studio | $0.25 / $1.50 |
| Larger open-weight family | DeepSeek V4.1 Flash | Fireworks | $0.22 / $0.66 |
| Smaller open-weight candidate | Qwen3.5 9B | DeepInfra BF16 | $0.10 / $0.15 |

Rates are endpoint snapshots on 2026-09-29; returned usage supplies measured billing. The DeepSeek direct route was incompatible with the account's existing data policy, so Fireworks was selected before any scored attempt. No account policy was changed. These hosted runs do not measure the feasibility or cost of local deployment in Africa.

Fable's documented coding and agent capabilities make it a useful expensive reference; Astra adds a second frontier family. Neither is selected because it is a weather prediction model. DeepSeek and Qwen test whether reusable scientific operations can make less expensive open-weight agents competitive. Sonnet and Flash-Lite provide intermediate and low-cost closed-weight comparisons. This panel spans capability, price and weight access; it is not a representative sample of all LLMs.

DeepSeek is a hosted or substantial institutional-compute candidate, not a small offline model: its [official model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) describes a 552B-parameter backbone, with 8B active during input processing and 16B during output generation, plus additional components. Active parameters are not the deployment memory footprint. Qwen 9B fills the smaller-model role; actual local hardware and network testing is still required.

Sources: [Fable model and endpoint documentation](https://openrouter.ai/anthropic/claude-fable-5.1), [Astra official model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra), [DeepSeek endpoint documentation](https://openrouter.ai/deepseek/deepseek-v4.1-flash), and the Sonnet, Flash-Lite and Qwen sources above. Astra's Chat Completions text mode supports this runner's JSON action protocol; the runner does not use native function calling. The common low reasoning setting prioritizes interactive latency and is not an equal-compute guarantee across vendors.

The expanded study removes one-shot Python, enforces skill use, and evaluates all ten existing task families. It remains a synthetic scientific-workflow diagnostic. African forecast-service deployment decisions still need frozen regional data, local network measurements, operational definitions agreed with meteorologists, and multilingual analyst evaluation where relevant.
