from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Hypothesis:
    id: str
    title: str
    segment: str
    hypothesis_class: str
    claim: str
    kill_rules: list[str]
    status: str
    rationale: str = ""
    pass_criteria: list[str] = field(default_factory=list)
    max_spend_usd: float = 0.0
    decision_date: str = ""
    experiments: list[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypothesis:
        return cls(
            id=data["id"],
            title=data["title"],
            segment=data["segment"],
            hypothesis_class=data["hypothesis_class"],
            claim=data["claim"],
            kill_rules=list(data["kill_rules"]),
            status=data["status"],
            rationale=data.get("rationale", ""),
            pass_criteria=list(data.get("pass_criteria", [])),
            max_spend_usd=float(data.get("max_spend_usd", 0)),
            decision_date=data.get("decision_date", ""),
            experiments=list(data.get("experiments", [])),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "segment": self.segment,
            "hypothesis_class": self.hypothesis_class,
            "claim": self.claim,
            "rationale": self.rationale,
            "pass_criteria": self.pass_criteria,
            "kill_rules": self.kill_rules,
            "max_spend_usd": self.max_spend_usd,
            "decision_date": self.decision_date,
            "status": self.status,
            "experiments": self.experiments,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Experiment:
    id: str
    hypothesis_id: str
    kind: str
    title: str
    claim: str
    method: str
    thresholds: dict[str, dict[str, Any]]
    failure_conditions: list[str]
    max_spend_usd: float
    decision_date: str
    status: str
    rationale: str = ""
    bias_risks: list[str] = field(default_factory=list)
    plugin_config: dict[str, Any] = field(default_factory=dict)
    hardware: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Experiment:
        return cls(
            id=data["id"],
            hypothesis_id=data["hypothesis_id"],
            kind=data["kind"],
            title=data["title"],
            claim=data["claim"],
            method=data["method"],
            thresholds=dict(data["thresholds"]),
            failure_conditions=list(data["failure_conditions"]),
            max_spend_usd=float(data["max_spend_usd"]),
            decision_date=data["decision_date"],
            status=data["status"],
            rationale=data.get("rationale", ""),
            bias_risks=list(data.get("bias_risks", [])),
            plugin_config=dict(data.get("plugin_config", {})),
            hardware=dict(data.get("hardware", {})),
            depends_on=list(data.get("depends_on", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "kind": self.kind,
            "title": self.title,
            "claim": self.claim,
            "rationale": self.rationale,
            "method": self.method,
            "bias_risks": self.bias_risks,
            "thresholds": self.thresholds,
            "failure_conditions": self.failure_conditions,
            "max_spend_usd": self.max_spend_usd,
            "decision_date": self.decision_date,
            "status": self.status,
            "plugin_config": self.plugin_config,
            "hardware": self.hardware,
            "depends_on": self.depends_on,
        }


@dataclass(frozen=True)
class RunArtifact:
    run_id: str
    experiment_id: str
    hypothesis_id: str
    kind: str
    git_sha: str
    started_at: str
    finished_at: str
    dry_run: bool
    metrics: dict[str, Any]
    outcome: str
    evaluation: dict[str, Any]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "hypothesis_id": self.hypothesis_id,
            "kind": self.kind,
            "git_sha": self.git_sha,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "metrics": self.metrics,
            "outcome": self.outcome,
            "evaluation": self.evaluation,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class DecisionRecord:
    hypothesis_id: str
    outcome: str
    memo: str
    recorded_at: str
    experiment_id: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "outcome": self.outcome,
            "memo": self.memo,
            "recorded_at": self.recorded_at,
        }
