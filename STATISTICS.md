# Metrics and statistical interpretation

## Why not Cohen's kappa as the headline?

[Cohen's kappa](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html) measures agreement beyond chance between two raters or classifiers. This benchmark has one deterministic numerical checker, not two subjective raters. Agreement between the skills and Python agents is also not the main question: they can agree because both fail. Against an answer key in which every task should pass, binary kappa degenerates: any imperfect result has kappa zero, and an all-pass result has an undefined denominator. It cannot distinguish 1/10 from 9/10 correct in that setup.

Use kappa later if independent human meteorologists classify generated warnings or explanations, alongside raw agreement and class frequencies. Do not replace task accuracy with kappa here.

## Primary metrics

- **Success rate:** fraction of evaluated tasks whose saved answer passes every numerical and structural assertion. Show counts and a **95% Wilson interval**, not just a percentage. Provider errors, timeouts and budget stops stay visible and in the denominator. Operator cancellations are unscored; their traces and spend remain visible. An answer already saved before a later API rejection can still pass the numerical check.
- **Latency:** median solve time and an inspectable per-run distribution. Model time, execution and setup remain separate in logs. Model averages exclude operator cancellations; the run log preserves their elapsed time. Timing is end-to-end for this harness, not tokens/second or local African-network latency.
- **Tokens:** total input plus output across all requests, including repeated history. Cached input and reasoning subsets are reported separately without double counting.
- **Cost:** billed USD per attempt and **cost per successful task** (all attempted spend divided by successes). Zero successes makes cost per success undefined, not free. Unknown charges remain unknown.
- **Adoption and workflow:** guide reads, actual skill calls, rejected code attempts, and artifact-based recipe conformance. Correctness and exact reference-conformance are separate outcomes.

The reporting structure follows the [SWE-bench leaderboard](https://www.swebench.com/) emphasis on task resolution and reproducible runs, and [Artificial Analysis](https://artificialanalysis.ai/methodology/intelligence-benchmarking)'s separation of measured capability and uncertainty. Their scores and confidence claims are not transferred to this benchmark.

## Paired comparisons

Match conditions on model, task and repetition. Report skills-only wins, Python-only wins, both-pass and both-fail counts, plus success difference in percentage points. Exclude pairs with a provider error or operator interruption on either side from the capability comparison; retain those runs in the operational totals. Report excluded counts in the exported statistics.

For one run per task, use the **two-sided exact McNemar test**, which considers discordant pairs. Conditional on their total, the null assigns equal probability to which arm succeeds. Use the exact binomial calculation, not a large-sample chi-squared approximation on tiny counts. [Statsmodels documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html)

Apply Holm correction across the planned six-model panel in the dashboard. Filtering to one model does not remove that multiplicity adjustment. Task-subset analysis is exploratory, not a fresh preregistered hypothesis.

Repeated attempts on the same task are clustered. Do not treat 3 repetitions × 10 fixtures as 30 independent task samples for McNemar. The export omits that p-value when fixtures repeat and offers a seeded task-level bootstrap of paired task-average differences. A degenerate all-equal bootstrap is omitted rather than presented as a zero-width uncertainty interval.

Wilson intervals assume independent Bernoulli task outcomes. With repeated fixtures they are descriptive attempt intervals, not valid task-generalization intervals; use a task-clustered analysis for that purpose. The current expanded study uses ten tasks and one repetition, so within-model samples are ten unique task fixtures.

## Limits

Ten deliberately chosen synthetic tasks do not form a random sample of African forecasting workflows. Confidence intervals and p-values cannot repair that sampling limitation. A non-significant difference is not evidence of equivalence, and a significant result would still apply to the tested task mix, prompts, catalog pin, routes and model settings.

Do not compute pass@k or take the best of repeated attempts when the intended user experience is one agent session with its ordinary internal retries. The unit here is the entire isolated agent session.

The dashboard now provides two explicit denominators. **Task outcomes** exclude
provider errors, interruptions and unverified sources from all comparison
averages. **All scored attempts** include provider errors, retaining the original
operational metric. Empty groups are missing outcomes, never zero success. Both
views retain all attempted charges in reported spend and all traces in coverage.
The JSON export supplies `task_outcome_statistics` alongside the original
`condition_statistics`; neither is a matched-pair estimate. The separate paired
analysis remains necessary when model/condition coverage differs.
