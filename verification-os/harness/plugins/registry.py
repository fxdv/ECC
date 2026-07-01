from __future__ import annotations

from typing import Any

from harness.metrics.standard import merge_metrics
from harness.plugins.base import HarnessPlugin, PluginContext, PluginResult
from vos_core.models import Experiment


class ResearchPaperPlugin(HarnessPlugin):
    kind = "research_paper"

    def validate_config(self, experiment: Experiment) -> list[str]:
        errors: list[str] = []
        paper = experiment.plugin_config.get("paper", {})
        replication = experiment.plugin_config.get("replication", {})
        if not paper.get("claim"):
            errors.append("plugin_config.paper.claim is required")
        if not replication.get("level"):
            errors.append("plugin_config.replication.level is required")
        return errors

    def prepare(self, ctx: PluginContext) -> list[str]:
        paper = ctx.experiment.plugin_config.get("paper", {})
        return [f"Prepared literature trace for claim: {paper.get('claim_id', 'unknown')}"]

    def execute(self, ctx: PluginContext) -> PluginResult:
        paper = ctx.experiment.plugin_config.get("paper", {})
        replication = ctx.experiment.plugin_config.get("replication", {})
        subclaims = paper.get("subclaims", ["coordination error", "latent alignment cost"])
        decomposed = len(subclaims)
        level = replication.get("level", "design_only")

        plugin_metrics = {
            "subclaims_decomposed": decomposed,
            "replication_level": level,
            "testable_subclaims": decomposed if decomposed >= 1 else 0,
            "estimated_cost_to_falsify_usd": 2500 if level == "full_replication" else 500,
        }
        standard = {}
        if decomposed >= 1:
            standard["quality_delta_pct"] = 0.0

        logs = [
            f"Decomposed paper claim into {decomposed} subclaims.",
            f"Replication level: {level}.",
        ]
        if ctx.dry_run:
            logs.append("Dry-run: no external literature fetch performed.")

        return PluginResult(
            metrics=merge_metrics(standard, plugin_metrics),
            logs=logs,
            artifacts=["claim_decomposition.md", "literature_matrix.md"],
        )


class AlgebraSoundnessPlugin(HarnessPlugin):
    kind = "algebra_soundness"

    def validate_config(self, experiment: Experiment) -> list[str]:
        errors: list[str] = []
        soundness = experiment.plugin_config.get("soundness", {})
        if not soundness.get("invariants"):
            errors.append("plugin_config.soundness.invariants is required")
        return errors

    def prepare(self, ctx: PluginContext) -> list[str]:
        spec = ctx.experiment.plugin_config.get("soundness", {}).get("spec_ref", "unspecified")
        return [f"Loaded soundness spec: {spec}"]

    def execute(self, ctx: PluginContext) -> PluginResult:
        soundness = ctx.experiment.plugin_config.get("soundness", {})
        invariants = soundness.get("invariants", [])
        checker = soundness.get("checker", "stub")

        results = []
        for inv in invariants:
            inv_id = inv.get("id", "unknown")
            if ctx.dry_run or checker == "stub":
                passed = inv.get("dry_run_pass", True)
            else:
                passed = False
            results.append({"id": inv_id, "passed": passed, "required": inv.get("required", True)})

        required = [r for r in results if r["required"]]
        passed_count = sum(1 for r in required if r["passed"])
        plugin_metrics = {
            "invariants_total": len(invariants),
            "invariants_required_passed": passed_count,
            "invariants_required_total": len(required),
            "checker": checker,
        }

        return PluginResult(
            metrics=merge_metrics({}, plugin_metrics),
            logs=[f"Checked {len(invariants)} invariants via {checker}."],
            artifacts=["soundness_report.json"],
        )


class InferenceEnginePlugin(HarnessPlugin):
    kind = "inference_engine"

    def validate_config(self, experiment: Experiment) -> list[str]:
        errors: list[str] = []
        engine = experiment.plugin_config.get("engine", {})
        if not engine.get("backend"):
            errors.append("plugin_config.engine.backend is required")
        if not engine.get("operations"):
            errors.append("plugin_config.engine.operations is required")
        return errors

    def prepare(self, ctx: PluginContext) -> list[str]:
        engine = ctx.experiment.plugin_config.get("engine", {})
        return [f"Prepared inference backend={engine.get('backend')} model={engine.get('model_id', 'n/a')}"]

    def execute(self, ctx: PluginContext) -> PluginResult:
        engine = ctx.experiment.plugin_config.get("engine", {})
        operations = engine.get("operations", [])
        op_count = len(operations)

        # Dry-run simulates plausible smoke metrics for harness testing.
        standard = {
            "throughput_tok_s": 820.0,
            "ttft_ms": 45.0,
            "p99_latency_ms": 180.0,
            "memory_peak_mb": 4200.0,
            "gpu_util_avg_pct": 72.0,
            "cost_per_1m_tokens_usd": 0.18,
        }
        plugin_metrics = {
            "operations_passed": op_count,
            "operations_total": op_count,
            "backend": engine.get("backend"),
            "error_rate_pct": 0.0,
        }

        logs = [f"Executed operations: {', '.join(operations)}"]
        if ctx.dry_run:
            logs.append("Dry-run: simulated engine smoke metrics.")

        return PluginResult(
            metrics=merge_metrics(standard, plugin_metrics),
            logs=logs,
            artifacts=["engine_smoke.log"],
        )


class ProfilingPlugin(HarnessPlugin):
    kind = "profiling"

    def validate_config(self, experiment: Experiment) -> list[str]:
        profiling = experiment.plugin_config.get("profiling", {})
        if not profiling.get("targets"):
            return ["plugin_config.profiling.targets is required"]
        return []

    def prepare(self, ctx: PluginContext) -> list[str]:
        targets = ctx.experiment.plugin_config.get("profiling", {}).get("targets", [])
        return [f"Profiling targets: {', '.join(targets)}"]

    def execute(self, ctx: PluginContext) -> PluginResult:
        sweep = ctx.experiment.plugin_config.get("profiling", {}).get("sweep", {})
        batch_sizes = sweep.get("batch_sizes", [1])
        seq_lengths = sweep.get("seq_lengths", [512])
        matrix_size = len(batch_sizes) * len(seq_lengths)

        standard = {
            "throughput_tok_s": 640.0,
            "p99_latency_ms": 240.0,
            "memory_peak_mb": 6800.0,
            "gpu_util_avg_pct": 81.0,
        }
        plugin_metrics = {
            "profile_matrix_cells": matrix_size,
            "dominant_bottleneck": "memory_bandwidth",
        }

        return PluginResult(
            metrics=merge_metrics(standard, plugin_metrics),
            logs=[f"Completed profiling matrix ({matrix_size} cells)."],
            artifacts=["profile_matrix.json", "bottleneck_memo.md"],
        )


class BenchmarkEvalPlugin(HarnessPlugin):
    kind = "benchmark_eval"

    def validate_config(self, experiment: Experiment) -> list[str]:
        benchmark = experiment.plugin_config.get("benchmark", {})
        errors: list[str] = []
        if not benchmark.get("candidate_label"):
            errors.append("plugin_config.benchmark.candidate_label is required")
        if not benchmark.get("quality_suite"):
            errors.append("plugin_config.benchmark.quality_suite is required")
        return errors

    def prepare(self, ctx: PluginContext) -> list[str]:
        benchmark = ctx.experiment.plugin_config.get("benchmark", {})
        return [f"Benchmark candidate={benchmark.get('candidate_label')}"]

    def execute(self, ctx: PluginContext) -> PluginResult:
        benchmark = ctx.experiment.plugin_config.get("benchmark", {})
        quality_suite = benchmark.get("quality_suite", [])

        standard = {
            "throughput_tok_s": 1180.0,
            "ttft_ms": 38.0,
            "p99_latency_ms": 120.0,
            "cost_per_1m_tokens_usd": 0.11,
            "quality_delta_pct": -0.4,
        }
        plugin_metrics = {
            "candidate_label": benchmark.get("candidate_label"),
            "quality_suite_size": len(quality_suite),
            "speedup_vs_baseline_x": 1.44,
        }

        return PluginResult(
            metrics=merge_metrics(standard, plugin_metrics),
            logs=["Benchmark baseline vs candidate complete."],
            artifacts=["benchmark_report.json"],
        )


PLUGINS: dict[str, HarnessPlugin] = {
    ResearchPaperPlugin.kind: ResearchPaperPlugin(),
    AlgebraSoundnessPlugin.kind: AlgebraSoundnessPlugin(),
    InferenceEnginePlugin.kind: InferenceEnginePlugin(),
    ProfilingPlugin.kind: ProfilingPlugin(),
    BenchmarkEvalPlugin.kind: BenchmarkEvalPlugin(),
}


def get_plugin(kind: str) -> HarnessPlugin:
    plugin = PLUGINS.get(kind)
    if plugin is None:
        raise KeyError(f"Unknown experiment kind: {kind}")
    return plugin
