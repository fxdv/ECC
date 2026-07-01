from __future__ import annotations

from pathlib import Path

import pytest

from harness.metrics.standard import evaluate_thresholds, merge_metrics
from harness.plugins.registry import get_plugin
from vos_core.experiment_runner import ExperimentRunner
from vos_core.ledger import Ledger
from vos_core.validate import validate_experiment, validate_hypothesis, load_yaml


ROOT = Path(__file__).resolve().parent.parent


def test_hypothesis_schema_example():
    data = load_yaml(ROOT / "data/hypotheses/h-001.yaml")
    assert validate_hypothesis(data) == []


def test_experiment_schema_examples():
    for name in ["e-001.yaml", "e-002.yaml", "e-003.yaml"]:
        data = load_yaml(ROOT / "data/experiments" / name)
        assert validate_experiment(data) == [], name


def test_all_plugins_registered():
    for kind in [
        "research_paper",
        "algebra_soundness",
        "inference_engine",
        "profiling",
        "benchmark_eval",
    ]:
        plugin = get_plugin(kind)
        assert plugin.kind == kind


def test_evaluate_thresholds_pass_and_fail():
    metrics = merge_metrics({"throughput_tok_s": 900}, {"speedup_vs_baseline_x": 1.5})
    passed = evaluate_thresholds(
        metrics,
        {
            "standard.throughput_tok_s": {"op": "gte", "value": 500},
            "plugin.speedup_vs_baseline_x": {"op": "gte", "value": 1.3},
        },
    )
    assert passed["passed"] is True

    failed = evaluate_thresholds(
        metrics,
        {"standard.throughput_tok_s": {"op": "gte", "value": 1000}},
    )
    assert failed["passed"] is False


def test_dry_run_research_paper_experiment():
    runner = ExperimentRunner(ROOT)
    artifact = runner.run(ROOT / "data/experiments/e-001.yaml", dry_run=True)
    assert artifact.outcome == "pass"
    assert (ROOT / "data/runs" / artifact.run_id / "metrics.json").exists()


def test_ledger_status_summary():
    ledger = Ledger(ROOT)
    summary = ledger.status_summary()
    assert summary["hypotheses"]["total"] >= 1
    assert summary["experiments"]["total"] >= 3
    assert "total" in summary["runs"]
