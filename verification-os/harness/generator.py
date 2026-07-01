from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vos_core.ledger import Ledger
from vos_core.models import Experiment
from vos_core.validate import validate_experiment


KIND_DEFAULTS: dict[str, dict[str, Any]] = {
    "research_paper": {
        "title_suffix": "Decompose paper claims",
        "method": "Literature matrix, claim decomposition, map subclaims to experiment kinds.",
        "thresholds": {
            "plugin.testable_subclaims": {"op": "gte", "value": 2},
            "plugin.estimated_cost_to_falsify_usd": {"op": "lte", "value": 5000},
        },
        "failure_conditions": [
            "Fewer than 2 testable subclaims",
            "All subclaims require full replication before bench test",
        ],
        "max_spend_usd": 500,
        "plugin_config": {
            "paper": {"title": "", "claim_id": "C1", "claim": "", "subclaims": []},
            "replication": {"level": "design_only", "artifacts": ["literature_matrix.md"]},
        },
    },
    "algebra_soundness": {
        "title_suffix": "Algebra invariant gate",
        "method": "Run required invariants against spec before integration.",
        "thresholds": {
            "plugin.invariants_required_passed": {"op": "gte", "value": 1},
        },
        "failure_conditions": ["Required invariant fails without waiver"],
        "max_spend_usd": 1000,
        "plugin_config": {
            "soundness": {
                "spec_ref": "specs/latent_buffer_invariants.md",
                "checker": "stub",
                "invariants": [],
            },
        },
    },
    "inference_engine": {
        "title_suffix": "Inference engine smoke",
        "method": "Load model, single request, batch request smoke on target backend.",
        "thresholds": {
            "standard.p99_latency_ms": {"op": "lte", "value": 500},
            "plugin.error_rate_pct": {"op": "lte", "value": 1.0},
        },
        "failure_conditions": ["Any operation errors", "p99 latency above threshold"],
        "max_spend_usd": 2000,
        "plugin_config": {
            "engine": {
                "backend": "vllm",
                "model_id": "meta-llama/Llama-3.2-1B-Instruct",
                "operations": ["load", "single_request", "batch_request"],
            },
        },
    },
    "profiling": {
        "title_suffix": "Performance profiling sweep",
        "method": "Sweep batch sizes and sequence lengths; record bottleneck memo.",
        "thresholds": {
            "plugin.profile_matrix_cells": {"op": "gte", "value": 1},
        },
        "failure_conditions": ["Profile matrix incomplete"],
        "max_spend_usd": 1500,
        "plugin_config": {
            "profiling": {
                "targets": ["latency", "memory", "gpu_util"],
                "sweep": {"batch_sizes": [1, 8, 32], "seq_lengths": [512, 2048]},
            },
        },
    },
    "benchmark_eval": {
        "title_suffix": "Baseline vs candidate benchmark",
        "method": "Compare candidate against preregistered baseline with quality gates.",
        "thresholds": {
            "plugin.speedup_vs_baseline_x": {"op": "gte", "value": 1.3},
            "standard.quality_delta_pct": {"op": "gte", "value": -1.0},
        },
        "failure_conditions": ["Speedup below 1.1x", "Quality regression >1%"],
        "max_spend_usd": 5000,
        "plugin_config": {
            "benchmark": {
                "baseline_ref": "",
                "candidate_label": "candidate_v0",
                "quality_suite": ["mmlu_subset"],
                "perf_metrics": ["throughput_tok_s", "p99_latency_ms", "cost_per_1m_tokens_usd"],
            },
        },
    },
}

CHAIN_BY_THESIS: dict[str, list[str]] = {
    "research_to_product": [
        "research_paper",
        "algebra_soundness",
        "inference_engine",
        "profiling",
        "benchmark_eval",
    ],
    "optimization_wedge": ["profiling", "benchmark_eval"],
    "paper_only": ["research_paper"],
}


@dataclass(frozen=True)
class HarnessSpec:
    hypothesis_id: str
    kind: str
    claim: str
    title: str = ""
    depends_on: list[str] | None = None
    plugin_config: dict[str, Any] | None = None
    thresholds: dict[str, Any] | None = None
    decision_date: str = "2026-12-31"


class HarnessGenerator:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.ledger = Ledger(root)

    def generate_experiment(self, spec: HarnessSpec, experiment_id: str | None = None) -> Experiment:
        if spec.kind not in KIND_DEFAULTS:
            raise ValueError(f"Unknown kind: {spec.kind}")

        defaults = KIND_DEFAULTS[spec.kind]
        exp_id = experiment_id or self.ledger.next_experiment_id()
        title = spec.title or f"{exp_id} — {defaults['title_suffix']}"

        plugin_config = _deep_merge(dict(defaults["plugin_config"]), spec.plugin_config or {})
        thresholds = spec.thresholds or dict(defaults["thresholds"])

        if spec.kind == "research_paper" and spec.claim:
            paper = plugin_config.setdefault("paper", {})
            paper["claim"] = spec.claim
            if not paper.get("subclaims"):
                paper["subclaims"] = [
                    "Mechanism preserves bounded error",
                    "Mechanism reduces overhead vs baseline",
                ]

        data: dict[str, Any] = {
            "id": exp_id,
            "hypothesis_id": spec.hypothesis_id,
            "kind": spec.kind,
            "title": title,
            "claim": spec.claim,
            "method": defaults["method"],
            "thresholds": thresholds,
            "failure_conditions": list(defaults["failure_conditions"]),
            "max_spend_usd": defaults["max_spend_usd"],
            "decision_date": spec.decision_date,
            "status": "preregistered",
            "plugin_config": plugin_config,
            "depends_on": list(spec.depends_on or []),
        }

        errors = validate_experiment(data)
        if errors:
            raise ValueError(f"Generated invalid experiment: {'; '.join(errors)}")

        experiment = Experiment.from_dict(data)
        self.ledger.save_experiment(experiment)
        return experiment

    def generate_chain(
        self,
        hypothesis_id: str,
        chain: str = "research_to_product",
        base_claim: str = "",
        paper_subclaims: list[str] | None = None,
    ) -> list[Experiment]:
        kinds = CHAIN_BY_THESIS.get(chain)
        if kinds is None:
            raise ValueError(f"Unknown chain: {chain}")

        created: list[Experiment] = []
        prev_id: str | None = None

        for kind in kinds:
            claim = base_claim or f"Verify {kind} for {hypothesis_id}"
            plugin_config: dict[str, Any] | None = None

            if kind == "research_paper":
                plugin_config = {
                    "paper": {
                        "title": "Generated from harness",
                        "claim_id": "C1",
                        "claim": base_claim or claim,
                        "subclaims": paper_subclaims
                        or [
                            "Mechanism preserves bounded error",
                            "Mechanism reduces overhead vs baseline",
                        ],
                    },
                }
            elif kind == "algebra_soundness":
                plugin_config = {
                    "soundness": {
                        "invariants": [
                            {
                                "id": "INV-1",
                                "statement": "Core operator preserves invariant",
                                "required": True,
                                "dry_run_pass": True,
                            },
                        ],
                    },
                }
            elif kind == "benchmark_eval":
                plugin_config = {
                    "benchmark": {"candidate_label": f"{hypothesis_id.lower()}_{kind}"},
                }

            spec = HarnessSpec(
                hypothesis_id=hypothesis_id,
                kind=kind,
                claim=claim,
                depends_on=[prev_id] if prev_id else [],
                plugin_config=plugin_config,
            )
            experiment = self.generate_experiment(spec)
            created.append(experiment)
            prev_id = experiment.id

        return created


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
