# VerificationOS Operating Guide

## Task routing

Every piece of work maps to **one hypothesis** and **one experiment kind**:

| Your work | Kind | First artifact |
|-----------|------|----------------|
| Read/decompose a paper (e.g. cross-agent latent conditioning) | `research_paper` | claim_decomposition.md |
| Prove algebra / invariants before integrating | `algebra_soundness` | soundness_report.json |
| Build or smoke-test inference backend | `inference_engine` | engine_smoke.log |
| Profile GPU/memory/latency sweeps | `profiling` | profile_matrix.json |
| Baseline vs candidate with quality gates | `benchmark_eval` | benchmark_report.json |

## Recommended chain for H-001-style theses

```
research_paper → algebra_soundness → inference_engine → profiling → benchmark_eval
     E-001            E-002              (optional)        (optional)      E-003
```

Skip or reorder by **cost-to-falsify**. Never start `inference_engine` before soundness passes if algebra is a kill criterion.

## Weekly loop

| Half-day | Mode | Actions |
|----------|------|---------|
| Mon AM | Discovery | Interviews; update hypothesis notes |
| Mon PM | Analysis | Synthesis memo; adjust kill rules |
| Tue | Build | Preregister + run experiments |
| Wed | Build | Engine/profiling/benchmark execution |
| Thu AM | Analysis | Read metrics.json; draft decision memo |
| Thu PM | Narrative | Grants, partner updates, specs |
| Fri | Buffer | Contractors, cloud, admin |

## Commands cheat sheet

```bash
vos status
vos run data/experiments/e-001.yaml --dry-run
vos run data/experiments/e-002.yaml --dry-run
vos run data/experiments/e-003.yaml --dry-run
vos harness pipeline --hypothesis H-001 --dry-run
vos dashboard --port 8080
vos decision record --hypothesis H-001 --outcome escalate --memo "Soundness passed; schedule partner benchmark"
```

## Promotion checklist

Before creating `ventures/<name>/`:

- [ ] `value` commitment on file (LOI / pilot / grant)
- [ ] Latest `technical` experiment outcome = `pass`
- [ ] Decision memo < 7 days old
- [ ] Reproducibility pack (config + metrics + hardware spec)

## Extending plugins for production

Replace dry-run stubs with real integrations:

| Plugin | Wire to |
|--------|---------|
| `inference_engine` | vLLM / Triton CLI, health checks |
| `profiling` | Nsight, PyTorch profiler, nvidia-smi sampling |
| `benchmark_eval` | Your eval harness + MLflow run IDs |
| `algebra_soundness` | Z3, Lean, or custom checker |
| `research_paper` | Literature DB + structured claim YAML |

Keep the **experiment schema unchanged** — only `plugin_config` and `execute()` internals evolve.
