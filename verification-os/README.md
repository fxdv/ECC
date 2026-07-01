# VerificationOS

A scope-agnostic **hypothesis-verification engine** for a solo deeptech AI studio. One orchestration layer for:

- Research papers (e.g. cross-agent latent conditioning)
- Algebra / formal soundness checks
- Inference engine development
- Model performance profiling
- Evaluation benchmarking

**Not** a product platform. VerificationOS unifies **evidence, experiments, and decisions** — venture code stays in isolated modules until a wedge passes criteria.

## Quick start

```bash
cd verification-os
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Register a hypothesis
vos hypothesis init --from templates/hypothesis.template.yaml

# Preregister an experiment
vos experiment init --kind benchmark_eval --hypothesis H-001

# Dry-run the harness (no GPU required)
vos run data/experiments/e-003.yaml --dry-run

# Record a decision
vos decision record --hypothesis H-001 --outcome escalate --memo "Baseline beat; partner pilot next"

# List ledger state
vos status

# Generate harness chain + run pipeline
vos harness chain --hypothesis H-001 --chain research_to_product --claim "Shared latent buffer reduces coordination error"
vos harness pipeline --hypothesis H-001 --dry-run

# Launch HI dashboard (http://127.0.0.1:8080)
vos dashboard --port 8080
```

## Architecture

```
verification-os/
├── vos_core/           # Layer 1 — permanent verification engine
├── harness/            # Generator, pipeline, plugins, metrics
├── dashboard/          # FastAPI + HI dashboard UI
├── data/               # Hypotheses, experiments, run artifacts
├── templates/          # Copy-paste starters
└── ventures/           # Promoted wedges (empty until pass criteria)
```

See [SPEC.md](./SPEC.md) for the full contract.

## Plugin kinds

| Kind | Use when |
|------|----------|
| `research_paper` | Literature → falsifiable claim → replication plan |
| `algebra_soundness` | Invariant / equational checks before promotion |
| `inference_engine` | Serving stack build, smoke, regression |
| `profiling` | Latency, memory, GPU utilization sweeps |
| `benchmark_eval` | Baseline vs candidate with quality gates |

## Harness commands

| Command | Purpose |
|---------|---------|
| `vos harness generate` | Create one preregistered experiment YAML from a claim |
| `vos harness chain` | Generate linked experiment chain (`research_to_product`, `optimization_wedge`, `paper_only`) |
| `vos harness pipeline` | Run hypothesis experiments in dependency order |

## HI Dashboard

The dashboard surfaces hypothesis pipelines, recent runs, decisions, and one-click dry-run execution.

```bash
vos dashboard --port 8080
```

API endpoints: `/api/overview`, `/api/hypotheses`, `/api/experiments`, `/api/runs`, `/api/decisions`

## Weekly workflow

1. **Discovery** — update hypothesis ledger from interviews
2. **Preregister** — experiment YAML before running
3. **Execute** — `vos run <experiment.yaml>`
4. **Decide** — kill / pivot / escalate with written memo
5. **Promote** — copy passing venture code to `ventures/` only after value + technical pass

## Design rules

- Same experiment schema for every domain
- Every run emits: config, git SHA, hardware spec, metrics JSON, decision hook
- Test the **riskiest, cheapest-to-falsify** assumption first
- No unified inference engine until a design partner pays
