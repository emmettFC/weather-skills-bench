# Provider recovery investigation

The original 30-attempt real-forecast pilot had **nine service failures** and **six Gemini response-format failures**. The initial dashboard grouped both under provider errors. Public exports now distinguish them; original responses and scores are preserved.

| Observed failure | Original attempts | Change in the independent recovery cohort |
|---|---:|---|
| Qwen on DeepInfra: HTTP 429, `engine_overloaded` | 5 | Tested Parasail primary, DeepInfra backup; explicit same-model allowlist |
| DeepSeek on Fireworks: HTTP 429 | 3 | Tested Wafer primary and Novita backup |
| Fable: OpenRouter credit-verification admission timeout | 1 | Bounded retries for transient HTTP errors |
| Gemini: `MALFORMED_FUNCTION_CALL` inside HTTP 200 | 6 | Explicit JSON output mode; unusable actions receive feedback without execution |

These are observed endpoint and protocol failures, not evidence of bad weather reasoning. DeepSeek's original 429s included two `RATE_LIMIT_EXCEEDED` errors and one `invalid_request_error`; the latter is deliberately not retried as a transient limit.

## Evidence before the new study

- `results/provider-recovery-probes.json`: 24 successful short requests across tested routes; two direct-DeepSeek requests rejected by the account's existing paid-training restriction. The privacy setting was not changed.
- `results/provider-confirmation-probes.json`: 16/16 short requests succeeded, including Fable, Astra, Wafer DeepSeek and DeepInfra Qwen.
- `results/gemini-response-replays.json`: replayed two actual failing requests without executing their actions. Both reproduced the original error without JSON mode. Both passed with JSON mode on the original provider, and both passed on Vertex global with JSON mode.

These probes establish compatibility, not task success or future availability. They are diagnostics and are excluded from benchmark scores. Their reported costs remain in the probe artifacts.

## Separate end-to-end validation

`configs/end-to-end-recovery-v2.json` fixes the new settings before running all 30 task/model/condition cells again. No original successes or failures are selectively replaced. Both arms receive the same JSON mode, transport policy and explicit rainfall clipping rule. Model IDs remain unchanged, and providers may differ, so the historical and new cohorts must not be pooled as repeated trials under the same protocol.

Retries consume the existing HTTP request allowance and solve-time budget. Completed agent actions are never repeated by a transport retry. All reported charges and tokens are retained; unknown charges remain marked incomplete and receive a conservative reserve. Same-model fallback is restricted to tested routes with price caps. Ambiguous network timeouts, authentication and validation errors are not automatically retried.

Current task outcomes and costs are generated from the study in [E2E_FINDINGS.md](E2E_FINDINGS.md). The dashboard exposes each attempt's actual provider, actions, model responses, retry count, wait time and billed usage. The integrity audit independently regrades saved answers and reconciles reported usage.

Routing behavior follows [OpenRouter provider selection](https://openrouter.ai/docs/guides/routing/provider-selection), including provider allowlists, priorities and per-million-token price caps. Retry handling follows [OpenRouter error documentation](https://openrouter.ai/docs/api_reference/errors-and-debugging). Google's [finish-reason reference](https://ai.google.dev/api/generate-content#FinishReason) distinguishes malformed generated calls from successful completions.

## Recovery of the remaining 15 transport failures

The completed 36-cell panel retained 15 terminal service errors: seven 120-second request timeouts, seven dropped connections (`RemoteProtocolError`), and one error-designated completion. The earlier retry policy handled HTTP status failures but deliberately did not retry ambiguous network failures. Those errors therefore bypassed its recovery path. The terminal-error display also used the last successful request's native finish reason as an error code; that presentation bug is corrected.

`configs/provider-error-retry-v2.json` registers exactly one new isolated attempt for all 15 provider-failed cells. Original passes and substantive task failures are not eligible. The original records and costs remain unchanged. This is a post-hoc recovery analysis, not a uniform-protocol replacement experiment or a best-of-N success rate.

The new transport streams responses, ignores SSE keepalive comments, gathers final usage, and rejects truncated streams without executing their partial action. Fresh HTTP connections avoid connection-pool reuse. Requests may take up to 300 seconds within the unchanged 1,200-second task deadline. Read timeouts, dropped connections and explicitly listed transient transport errors share the existing bounded retry allowance. Retrying sends the same pending model request; prior tool actions are not repeated. Unknown charges receive spend reserves, and unknown token use receives a conservative input-byte-plus-output allowance against the task token limit. Confirmed partial-response usage is retained when available.

`results/streaming-provider-probes.json` records successful streaming delivery and usage on all six routes with a 1,024-output-token diagnostic cap. Two responses reached that diagnostic output cap; these are transport checks, not task passes. None of their generated actions was executed. The full retries retain the original 8,192-output-token limit.

The default recovery dashboard retains the original 21 task outcomes, displays pending replacements until each retry finishes, and links replacement runs to their original failures. It never chooses whichever attempt scored better. Reported total spend includes original failures and retries; chart averages describe the displayed attempts and therefore do not include all recovery overhead. Original cohorts and the standalone 15-attempt retry batch remain separately selectable.

### Long-output diagnosis and continuation

Streaming exposed a different cause behind a Qwen timeout: the provider was emitting a very long, repeated list of invalid actions. The 300-second request ceiling interrupted generation before its output-token limit, so this was not a silent service outage. The in-flight retry was operator-interrupted and remains unscored in `20260930T131715Z-4b5833`, including its known cost and reserves for unconfirmed requests. The four completed retry outcomes are retained.

`results/qwen-stream-route-probe.json` records a streamed check of the same long context on DeepInfra, with a 1,024-token diagnostic output cap. It completed in about 48 seconds with returned usage. The remaining cells resume with DeepInfra preferred for Qwen and a 600-second request ceiling inside the unchanged 1,200-second task deadline. This lets slow/long generation reach its normal output or task budget instead of prematurely treating it as a provider outage. It does not guarantee task success. The resumption records its code revisions and preserves the original interrupted batch.

The resumed Qwen heat attempt returned two full 8,192-token responses, each ending at the output limit with invalid, unterminated JSON. One took about 446 seconds; the next took about 516 seconds. A subsequent request reached the overall 1,200-second task deadline. The raw HTTP timeout remains in its trace, but the reported outcome is a task timeout and counts as a failure. It is not eligible for another provider-error retry. The completed Astra revision and heat replacements both passed. These interim outcomes establish delivery and classification improvements, not a final recovery success rate.

The retry worker refreshes the dashboard and standalone HTML after completed attempts. At completion, `scripts/audit_provider_recovery.py` checks that the 21 original task outcomes are unchanged, every replacement corresponds to an eligible original failure, original traces remain linked, and total spend retains original and retry charges. Its machine-readable result is `results/provider-recovery-audit.json`; `complete` must be true before treating its counts as final. Historical unknown charges remain unknown.
