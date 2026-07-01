from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vos_core.models import DecisionRecord, Experiment, Hypothesis
from vos_core.validate import dump_json, dump_yaml, load_yaml, validate_experiment, validate_hypothesis


class Ledger:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.hypotheses_dir = root / "data" / "hypotheses"
        self.experiments_dir = root / "data" / "experiments"
        self.runs_dir = root / "data" / "runs"
        self.decisions_dir = root / "data" / "decisions"

    def list_hypotheses(self) -> list[Hypothesis]:
        if not self.hypotheses_dir.exists():
            return []
        items = []
        for path in sorted(self.hypotheses_dir.glob("*.yaml")):
            data = load_yaml(path)
            errors = validate_hypothesis(data)
            if errors:
                raise ValueError(f"Invalid hypothesis {path.name}: {'; '.join(errors)}")
            items.append(Hypothesis.from_dict(data))
        return items

    def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        path = self.hypotheses_dir / f"{hypothesis_id.lower()}.yaml"
        if not path.exists():
            matches = list(self.hypotheses_dir.glob(f"{hypothesis_id}*.yaml"))
            if not matches:
                return None
            path = matches[0]
        data = load_yaml(path)
        return Hypothesis.from_dict(data)

    def save_hypothesis(self, hypothesis: Hypothesis) -> Path:
        errors = validate_hypothesis(hypothesis.to_dict())
        if errors:
            raise ValueError(f"Invalid hypothesis: {'; '.join(errors)}")
        path = self.hypotheses_dir / f"{hypothesis.id.lower()}.yaml"
        dump_yaml(path, hypothesis.to_dict())
        return path

    def list_experiments(self) -> list[Experiment]:
        if not self.experiments_dir.exists():
            return []
        items = []
        for path in sorted(self.experiments_dir.glob("*.yaml")):
            data = load_yaml(path)
            errors = validate_experiment(data)
            if errors:
                raise ValueError(f"Invalid experiment {path.name}: {'; '.join(errors)}")
            items.append(Experiment.from_dict(data))
        return items

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        path = self.experiments_dir / f"{experiment_id.lower()}.yaml"
        if not path.exists():
            matches = list(self.experiments_dir.glob(f"{experiment_id}*.yaml"))
            if not matches:
                return None
            path = matches[0]
        data = load_yaml(path)
        return Experiment.from_dict(data)

    def save_experiment(self, experiment: Experiment) -> Path:
        errors = validate_experiment(experiment.to_dict())
        if errors:
            raise ValueError(f"Invalid experiment: {'; '.join(errors)}")
        path = self.experiments_dir / f"{experiment.id.lower()}.yaml"
        dump_yaml(path, experiment.to_dict())

        hypothesis = self.get_hypothesis(experiment.hypothesis_id)
        if hypothesis and experiment.id not in hypothesis.experiments:
            updated = replace(
                hypothesis,
                experiments=[*hypothesis.experiments, experiment.id],
            )
            self.save_hypothesis(updated)
        return path

    def next_hypothesis_id(self) -> str:
        existing = self.list_hypotheses()
        if not existing:
            return "H-001"
        numbers = [int(h.id.split("-")[1]) for h in existing]
        return f"H-{max(numbers) + 1:03d}"

    def next_experiment_id(self) -> str:
        existing = self.list_experiments()
        if not existing:
            return "E-001"
        numbers = [int(e.id.split("-")[1]) for e in existing]
        return f"E-{max(numbers) + 1:03d}"

    def next_run_id(self) -> str:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        existing = list(self.runs_dir.glob("R-*"))
        if not existing:
            return "R-00001"
        numbers = [int(path.name.split("-")[1]) for path in existing]
        return f"R-{max(numbers) + 1:05d}"

    def record_decision(self, record: DecisionRecord) -> Path:
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        stamp = record.recorded_at.replace(":", "").replace("-", "")
        path = self.decisions_dir / f"{record.hypothesis_id.lower()}_{stamp}.json"
        dump_json(path, record.to_dict())
        return path

    def list_runs(self) -> list[dict[str, Any]]:
        if not self.runs_dir.exists():
            return []
        runs: list[dict[str, Any]] = []
        for decision_path in sorted(self.runs_dir.glob("R-*/decision.json")):
            run_id = decision_path.parent.name
            data = json.loads(decision_path.read_text(encoding="utf-8"))
            manifest_path = decision_path.parent / "manifest.json"
            manifest = {}
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            runs.append({**manifest, **data})
        return sorted(runs, key=lambda r: r.get("started_at", ""), reverse=True)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run_dir = self.runs_dir / run_id
        decision_path = run_dir / "decision.json"
        if not decision_path.exists():
            return None
        payload: dict[str, Any] = json.loads(decision_path.read_text(encoding="utf-8"))
        for name in ("manifest.json", "metrics.json"):
            path = run_dir / name
            if path.exists():
                payload[name.replace(".json", "")] = json.loads(path.read_text(encoding="utf-8"))
        logs_path = run_dir / "logs.txt"
        if logs_path.exists():
            payload["logs"] = logs_path.read_text(encoding="utf-8").splitlines()
        return payload

    def list_decisions(self) -> list[dict[str, Any]]:
        if not self.decisions_dir.exists():
            return []
        items = []
        for path in sorted(self.decisions_dir.glob("*.json"), reverse=True):
            items.append(json.loads(path.read_text(encoding="utf-8")))
        return items

    def experiments_for_hypothesis(self, hypothesis_id: str) -> list[Experiment]:
        return [e for e in self.list_experiments() if e.hypothesis_id == hypothesis_id]

    def latest_run_for_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        matches = [r for r in self.list_runs() if r.get("experiment_id") == experiment_id]
        return matches[0] if matches else None

    def status_summary(self) -> dict[str, Any]:
        hypotheses = self.list_hypotheses()
        experiments = self.list_experiments()
        runs = self.list_runs()
        decisions = self.list_decisions()
        outcomes = [r.get("outcome") for r in runs if r.get("outcome")]
        return {
            "hypotheses": {
                "total": len(hypotheses),
                "active": sum(1 for h in hypotheses if h.status == "active"),
                "killed": sum(1 for h in hypotheses if h.status == "killed"),
                "promoted": sum(1 for h in hypotheses if h.status == "promoted"),
            },
            "experiments": {
                "total": len(experiments),
                "preregistered": sum(1 for e in experiments if e.status == "preregistered"),
                "completed": sum(1 for e in experiments if e.status == "completed"),
            },
            "runs": {
                "total": len(runs),
                "pass": sum(1 for o in outcomes if o == "pass"),
                "fail": sum(1 for o in outcomes if o == "fail"),
                "ambiguous": sum(1 for o in outcomes if o == "ambiguous"),
            },
            "decisions": len(decisions),
        }

    def dashboard_snapshot(self) -> dict[str, Any]:
        hypotheses = [h.to_dict() for h in self.list_hypotheses()]
        experiments = [e.to_dict() for e in self.list_experiments()]
        runs = self.list_runs()[:20]
        decisions = self.list_decisions()[:10]

        pipelines = []
        for hypothesis in self.list_hypotheses():
            exps = self.experiments_for_hypothesis(hypothesis.id)
            pipelines.append(
                {
                    "hypothesis_id": hypothesis.id,
                    "title": hypothesis.title,
                    "status": hypothesis.status,
                    "experiments": [
                        {
                            "id": e.id,
                            "kind": e.kind,
                            "title": e.title,
                            "status": e.status,
                            "depends_on": e.depends_on,
                            "latest_run": self.latest_run_for_experiment(e.id),
                        }
                        for e in exps
                    ],
                }
            )

        return {
            "summary": self.status_summary(),
            "hypotheses": hypotheses,
            "experiments": experiments,
            "recent_runs": runs,
            "recent_decisions": decisions,
            "pipelines": pipelines,
            "generated_at": self.utc_now(),
        }

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
