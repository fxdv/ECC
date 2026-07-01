# VerificationOS Specification

Version 0.1 • July 2026

## Purpose

VerificationOS is the **Layer 1 operating system** for a solo deeptech AI studio. It orchestrates progress across heterogeneous work — from a scientific paper on cross-agent latent conditioning to algebra soundness gates, inference engine builds, profiling sweeps, and benchmark evaluation — without collapsing them into one premature product.

## Non-goals

- Multi-tenant SaaS inference platform
- Universal model compiler
- Auto-generated harness for every domain on day one
- Replacing MLflow, vLLM, or proof assistants (wrap and track them)

## Core concepts

### Hypothesis

A venture thesis under test. Five **classes** (risk-ranked ladder, not fixed order):

| Class | Question |
|-------|----------|
| `problem` | Is the pain real, costly, frequent? |
| `value` | Will someone commit if solved? |
| `technical` | Does the core mechanism work? |
| `operational` | Can it be produced and used safely? |
| `scalability` | Can this become a venture? |

### Experiment

A preregistered test linked to one hypothesis. Fields are **domain-agnostic**; domain specifics live in `plugin_config`.

### Run artifact

Immutable output bundle:

```
data/runs/<run_id>/
├── manifest.json       # git SHA, timestamps, plugin kind
├── config.resolved.yaml
├── metrics.json
├── logs/
└── decision.json       # pass | fail | ambiguous + next action
```

### Plugin

A domain adapter implementing the harness contract:

1. `validate_config` — reject bad configs before spend
2. `prepare` — staging, fixtures, env checks
3. `execute` — run work (or dry-run stub)
4. `collect_metrics` — normalize to standard + plugin metrics
5. `evaluate` — compare to preregistered thresholds

## Experiment kinds

### `research_paper`

Trace a paper claim to a falsifiable studio hypothesis.

```yaml
plugin_config:
  paper:
    title: "Cross-Agent Latent Conditioning for ..."
    claim_id: "C1"
    claim: "Shared latent buffer reduces coordination error vs message passing"
  replication:
    level: design_only  # design_only | simulation | full_replication
    artifacts: [literature_matrix.md, claim_decomposition.md]
```

**Pass example:** claim decomposed into ≥1 testable sub-claim with acceptance criteria and estimated cost-to-falsify.

### `algebra_soundness`

Gate optimizations or architecture changes.

```yaml
plugin_config:
  soundness:
    spec_ref: specs/latent_buffer_invariants.md
    checker: stub  # stub | z3 | custom
    invariants:
      - id: INV-1
        statement: "Projection preserves latent norm bound"
        required: true
```

**Pass example:** all `required: true` invariants pass or are explicitly waived with rationale.

### `inference_engine`

Build / smoke / regression for a serving stack.

```yaml
plugin_config:
  engine:
    backend: vllm  # vllm | triton | custom
    model_id: meta-llama/Llama-3.2-1B-Instruct
    operations: [load, single_request, batch_request]
```

**Pass example:** all operations complete; p99 latency and error rate under thresholds.

### `profiling`

Resource and latency characterization.

```yaml
plugin_config:
  profiling:
    targets: [latency, memory, gpu_util]
    sweep:
      batch_sizes: [1, 8, 32]
      seq_lengths: [512, 2048, 8192]
```

**Pass example:** profile matrix complete; bottleneck memo produced.

### `benchmark_eval`

Baseline vs candidate with quality gates.

```yaml
plugin_config:
  benchmark:
    baseline_ref: runs/R-00042/metrics.json
    candidate_label: awq_int4_v1
    quality_suite: [mmlu_subset, golden_rag_v1]
    perf_metrics: [throughput_tok_s, ttft_ms, p99_latency_ms, cost_per_1m_tokens]
```

**Pass example:** candidate meets **all** preregistered perf and quality thresholds vs baseline.

## Standard metrics envelope

Every run includes:

```json
{
  "standard": {
    "throughput_tok_s": null,
    "ttft_ms": null,
    "p99_latency_ms": null,
    "memory_peak_mb": null,
    "gpu_util_avg_pct": null,
    "cost_per_1m_tokens_usd": null,
    "quality_delta_pct": null
  },
  "plugin": {}
}
```

Nulls are allowed when not applicable; `evaluate` uses only metrics referenced in thresholds.

## Decision outcomes

| Outcome | Meaning |
|---------|---------|
| `pass` | Thresholds met — escalate or promote |
| `fail` | Kill criterion hit — stop or pivot |
| `ambiguous` | Narrow next experiment required |
| `waived` | Human override with documented rationale |

## Promotion rule

Code may move from `harness/plugins/` experiments into `ventures/<name>/` only when:

1. Hypothesis has `value` commitment signal (LOI, pilot, grant), **and**
2. Latest `technical` experiment `pass`, **and**
3. Decision memo recorded within 7 days

## CLI commands

| Command | Action |
|---------|--------|
| `vos hypothesis init` | Create hypothesis from template |
| `vos hypothesis list` | Show ledger |
| `vos experiment init` | Create preregistered experiment |
| `vos run <path>` | Execute experiment |
| `vos decision record` | Append decision memo |
| `vos status` | Dashboard summary |

## File conventions

- IDs: `H-###` hypotheses, `E-###` experiments, `R-#####` runs
- YAML for human-edited config; JSON for machine artifacts
- Git SHA captured at run time via `git rev-parse HEAD`

## Extension guide

Add a plugin:

1. Create `harness/plugins/my_kind.py` subclassing `HarnessPlugin` in `vos_core`-compatible layout
2. Register in `harness/plugins/registry.py`
3. Add example under `data/experiments/`
4. Test with `--dry-run` first

Keep plugins thin: call external tools (vLLM, Z3, pytest) from `execute`, normalize in `collect_metrics`.
