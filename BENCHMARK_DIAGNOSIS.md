# Why Python is competitive, and what the smaller-model extension tests

The current suite is a component-level diagnostic. It does not yet support a claim that the catalog improves end-to-end operational forecasting workflows.

## Evidence from the task definitions and traces

1. **The task brief supplies much of the scientific plan.** For example, rainfall-completeness explicitly specifies seven-day windows, the incomplete-period rule, the spatial bounds and cosine-latitude weighting. Ensemble spread specifies the flux conversion, order of aggregation, and ddof=1. These rules belong in deterministic acceptance criteria, but spelling out the complete procedure reduces the reasoning and discovery work being tested.
2. **Inputs are small, organized synthetic Zarr datasets.** Both agents receive variable names, dimensions, units and coordinate values in the prompt. The benchmark does not currently require retrieving heterogeneous provider products, identifying undocumented conventions, resolving revisions, or producing an operationally useful briefing with provenance.
3. **Python is a capable scientific environment.** NumPy, xarray, pandas, cftime, pint and other libraries are installed. The model writes a program; those libraries execute the arithmetic. This is an appropriate iterative coding-agent comparator and should not be crippled to make skills look better.
4. **A concrete small-model success is ordinary numerical programming.** Qwen3.5 9B's Python legacy-accumulation run (`e2bd43acde0d4016b509ef432aedb5ff`) inspected the dataset, calculated differences, sums and medians, then submitted the answer in three model calls. This is a legitimate pass, not evidence of answer-key access. Fixture hashes and sandbox boundaries are audited.
5. **Skill orchestration adds work.** The agent reads guides, selects CLI flags, chains artifacts and submits references. These costs can exceed writing a short array expression. Some failures occur before any calculation because the JSON action is malformed; others are CLI errors, output-contract failures or provider outages. They must not all be described as weather-reasoning failures.
6. **Cheap does not mean weak.** DeepSeek V4.1 Flash is a large MoE, not a small dense model. In the supplied screenshot, the genuinely smaller Qwen baseline passes only 2/6 and Gemini passes 4/6. Most perfect rates belong to strong models and still-small samples. The screenshot also compares unequal task coverage; use matched pairs for a skill effect.

## Prespecified smaller-model extension

`configs/small-models-v2.json` selects **Llama 3.2 1B Instruct and 3B Instruct**, both on Cloudflare, all ten existing tasks, both current conditions, one repetition: **40 attempts**. Both passed an API/JSON-action preflight. The same family and provider reduce some cross-model confounding; parameter count still does not isolate every training difference.

The extension keeps the same task fixtures, prompts, grader, 24-response/24-execution limits, 250,000 cumulative-token allowance and 600-second task deadline. Both models and both conditions share a 160,000-byte conversation limit, reduced from the main panel's 220,000 bytes to leave more room within the 1B provider's smaller context window. Byte limits are not exact tokenizer counts; endpoint context errors remain observable. The spend stop threshold is $2, checked between requests. There is no supported reasoning-effort parameter on these routes.

The experiment runs after the existing panel finishes, uses fresh isolated task sessions and appears separately in the dashboard. It does not replace failed existing runs or pool different coverage into a single success rate. Queue status is in `results/small-model-queue.json`; preflight evidence is in `results/preflight-small-models.json`. Results and the final audit are generated automatically.

Smaller models may improve the contrast, or may struggle even more with guide selection and command composition. Either outcome is evidence. Finding a model that fails without skills is not itself proof of catalog value.

## Next task-design priority

Retain this diagnostic suite, then add a separately versioned operational suite sampled from actual African weather-service requests. Give both conditions the same frozen source data and source documentation. Describe the requested product and scientifically necessary definitions without supplying the execution recipe. Test identification of accumulation/reset conventions, calendar and valid-time alignment, grid/catchment alignment, missing-data decisions, ensemble probabilities and auditable provenance. Establish answers independently and verify that actual catalog workflows can solve every case.

Also evaluate a production-style structured tool interface as a separate factor. Formatting failures in the current text-JSON harness can obscure the distinction between scientific ability and tool orchestration. Neither harder tasks nor a better adapter should be retroactively substituted into the ongoing study.

Sources: [Meta 1B model card](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct), [Meta 3B model card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct), [DeepSeek model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash). Current provider capabilities and prices were checked through OpenRouter's model and endpoint APIs on 2026-09-29. The benchmark-specific findings above are from local task definitions and recorded traces.
