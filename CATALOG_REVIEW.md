# Catalog review and coverage

Reviewed catalog commit `1a0af7de3bba2d7a6c4fe67f291eb0e58640b5f5`: **37 weather-skills and 4 chc-skills**. All skill discovery descriptions were reviewed; transformation guides, scripts, and runtime behavior were examined in detail for the reference suite. The first suite exercises 14 transformation skills, including one CHC skill, in ten scientific cases. Two more utilities (`inspect-zarr` and `provenance`) are exposed for agent discovery and auditing.

## Scope decisions

Prioritize numerical transformations where independent answers and ordering constraints can be specified exactly. Synthetic inputs remove availability, bandwidth, permission, and moving-source effects from the main experiment. A fetcher skill is not relabeled as a local fixture loader: that would benchmark a substitute implementation rather than the catalog.

Fetchers are candidates for a later separate retrieval suite using frozen upstream HTTP/Zarr snapshots and the actual fetcher code. Both conditions must receive the same frozen source access. Live network retrieval should be reported separately because latency and outputs vary. Time resolution needs an explicit frozen clock; geographic resolution needs a frozen gazetteer/boundary source. Plotting can be graded for selected data, units, axes, and embedded provenance, but not by raw PNG hash across rendering libraries. Pure image fetchers and feedback submission do not currently add a challenging, deterministic multi-step numerical case.

## Runtime findings (catalog unchanged)

- `unit-convert --to-units` fails with “no units attr” at this pin because core quantifies inputs and the script reads attrs. `--to-standard` works for the precipitation and air-temperature cases. Reference recipes use the supported path; the agents receive the original documentation with no privileged workaround hints.
- `concat` documentation shows repeated `-i`, but the actual script uses `nargs='+'`. Repeated flags retain only the final input. The working syntax is `--input a.zarr b.zarr c.zarr`. Reference execution verifies the real behavior.
- `aggregate-temporal --variable precip` drops a data-variable `time_bounds` before the duration-weighted path. For the irregular-interval case, leave `--variable` unset so bounds survive and are consumed correctly.
- `deaccumulate` and `step-to-time` declare a gridded forecast contract that requires latitude/longitude dimensions. Reference inputs satisfy that contract; the initial draft station-only fixtures were corrected before model evaluation.
- Several guides describe stronger validation than their current short scripts implement. The benchmark makes only claims demonstrated by execution, and does not copy catalog output into its oracle.

These findings are local documentation, not issues submitted to another repository. Core and catalog remain separately pinned, since each script's floating `@main` dependency would otherwise permit drift.

## Skill inventory

| Provider | Skill | v1 treatment |
|---|---|---|
| chc-skills | `africa-itf` | Deferred: requires frozen upstream sources or credentials |
| chc-skills | `iod-mode-index` | Executed in a validated reference case |
| chc-skills | `mjo-forecast-fetch` | Deferred: requires frozen upstream sources or credentials |
| chc-skills | `subc-mme-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `aggregate-temporal` | Executed in a validated reference case |
| weather-skills | `arco-era5-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `chirps-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `clip-region` | Executed in a validated reference case |
| weather-skills | `cmip6-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `coarsen` | Executed in a validated reference case |
| weather-skills | `concat` | Executed in a validated reference case |
| weather-skills | `convert-calendar` | Executed in a validated reference case |
| weather-skills | `convert-to-totals` | Executed in a validated reference case |
| weather-skills | `deaccumulate` | Executed in a validated reference case |
| weather-skills | `difference` | Executed in a validated reference case |
| weather-skills | `downscale` | Candidate for a later transformation case |
| weather-skills | `dynamical-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `ecmwf-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `ghcn-daily-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `imerg-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `inspect-zarr` | Available to agents; not required for reference conformance |
| weather-skills | `kenya-forecast-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `kenya-forecast-png` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `oisst-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `openaq-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `plot` | Deferred: semantic figure assertions needed |
| weather-skills | `plot-compare` | Deferred: semantic figure assertions needed |
| weather-skills | `plot-compare-forecasts` | Deferred: semantic figure assertions needed |
| weather-skills | `plot-mediogram` | Deferred: semantic figure assertions needed |
| weather-skills | `plot-timeseries` | Deferred: semantic figure assertions needed |
| weather-skills | `provenance` | Available to agents; not required for reference conformance |
| weather-skills | `rename` | Executed in a validated reference case |
| weather-skills | `resolve-region` | Deferred: freeze clock/gazetteer first |
| weather-skills | `resolve-time` | Deferred: freeze clock/gazetteer first |
| weather-skills | `select` | Executed in a validated reference case |
| weather-skills | `smap-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `step-to-time` | Executed in a validated reference case |
| weather-skills | `submit-feedback` | Excluded: not a scientific analysis task |
| weather-skills | `summarize-dim` | Executed in a validated reference case |
| weather-skills | `tahmo-fetch` | Deferred: requires frozen upstream sources or credentials |
| weather-skills | `unit-convert` | Executed in a validated reference case |
