from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from vos_core.models import Experiment


@dataclass(frozen=True)
class PluginContext:
    experiment: Experiment
    run_id: str
    run_dir: str
    dry_run: bool
    git_sha: str


@dataclass(frozen=True)
class PluginResult:
    metrics: dict[str, Any]
    logs: list[str]
    artifacts: list[str]


class HarnessPlugin(ABC):
    kind: str

    @abstractmethod
    def validate_config(self, experiment: Experiment) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def prepare(self, ctx: PluginContext) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, ctx: PluginContext) -> PluginResult:
        raise NotImplementedError

    def evaluate(self, experiment: Experiment, metrics: dict[str, Any]) -> dict[str, Any]:
        from harness.metrics.standard import evaluate_thresholds

        return evaluate_thresholds(metrics, experiment.thresholds)

    def next_action(self, outcome: str, experiment: Experiment) -> str:
        if outcome == "pass":
            return "Escalate: seek design-partner commitment or dependent experiment."
        if outcome == "fail":
            return f"Kill or pivot: review failure_conditions for {experiment.id}."
        return "Run narrower follow-up experiment to reduce ambiguity."
