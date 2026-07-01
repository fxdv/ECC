from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vos_core.experiment_runner import ExperimentRunner
from vos_core.ledger import Ledger
from vos_core.models import RunArtifact


@dataclass(frozen=True)
class PipelineResult:
    hypothesis_id: str
    stopped_at: str | None
    outcomes: list[dict[str, str]]
    completed: bool


class HarnessPipeline:
    """Run experiments for a hypothesis in dependency order."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.ledger = Ledger(root)
        self.runner = ExperimentRunner(root)

    def ordered_experiments(self, hypothesis_id: str) -> list:
        experiments = self.ledger.experiments_for_hypothesis(hypothesis_id)
        by_id = {e.id: e for e in experiments}
        ordered: list = []
        visited: set[str] = set()

        def visit(exp_id: str) -> None:
            if exp_id in visited:
                return
            visited.add(exp_id)
            exp = by_id.get(exp_id)
            if exp is None:
                return
            for dep in exp.depends_on:
                visit(dep)
            ordered.append(exp)

        for experiment in sorted(experiments, key=lambda e: e.id):
            visit(experiment.id)

        return ordered

    def run(
        self,
        hypothesis_id: str,
        *,
        dry_run: bool = False,
        stop_on_fail: bool = True,
        experiment_ids: list[str] | None = None,
    ) -> PipelineResult:
        ordered = self.ordered_experiments(hypothesis_id)
        if experiment_ids:
            allowed = set(experiment_ids)
            ordered = [e for e in ordered if e.id in allowed]

        outcomes: list[dict[str, str]] = []
        stopped_at: str | None = None

        for experiment in ordered:
            exp_path = self.ledger.experiments_dir / f"{experiment.id.lower()}.yaml"
            artifact: RunArtifact = self.runner.run(exp_path, dry_run=dry_run)
            outcomes.append(
                {
                    "experiment_id": experiment.id,
                    "run_id": artifact.run_id,
                    "outcome": artifact.outcome,
                    "kind": experiment.kind,
                }
            )
            if stop_on_fail and artifact.outcome == "fail":
                stopped_at = experiment.id
                break

        completed = stopped_at is None and len(outcomes) == len(ordered)
        return PipelineResult(
            hypothesis_id=hypothesis_id,
            stopped_at=stopped_at,
            outcomes=outcomes,
            completed=completed,
        )
