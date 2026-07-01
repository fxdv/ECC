from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from vos_core.ledger import Ledger
from vos_core.models import RunArtifact
from vos_core.validate import dump_json, dump_yaml, load_yaml, validate_experiment


class ExperimentRunner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.ledger = Ledger(root)

    def run(self, experiment_path: Path, dry_run: bool = False) -> RunArtifact:
        data = load_yaml(experiment_path)
        errors = validate_experiment(data)
        if errors:
            raise ValueError(f"Invalid experiment: {'; '.join(errors)}")

        experiment = self.ledger.get_experiment(data["id"])
        if experiment is None:
            from vos_core.models import Experiment

            experiment = Experiment.from_dict(data)

        from harness.plugins.registry import get_plugin

        plugin = get_plugin(experiment.kind)
        config_errors = plugin.validate_config(experiment)
        if config_errors:
            raise ValueError(f"Invalid plugin config: {'; '.join(config_errors)}")

        run_id = self.ledger.next_run_id()
        run_dir = self.ledger.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        git_sha = self._git_sha()
        started_at = Ledger.utc_now()

        from harness.plugins.base import PluginContext

        ctx = PluginContext(
            experiment=experiment,
            run_id=run_id,
            run_dir=str(run_dir),
            dry_run=dry_run,
            git_sha=git_sha,
        )

        prep_logs = plugin.prepare(ctx)
        result = plugin.execute(ctx)
        evaluation = plugin.evaluate(experiment, result.metrics)

        if evaluation["passed"]:
            outcome = "pass"
        elif any(v is None for v in evaluation["checks"].values() if not v["passed"]):
            outcome = "ambiguous"
        else:
            outcome = "fail"

        next_action = plugin.next_action(outcome, experiment)
        finished_at = Ledger.utc_now()

        artifact = RunArtifact(
            run_id=run_id,
            experiment_id=experiment.id,
            hypothesis_id=experiment.hypothesis_id,
            kind=experiment.kind,
            git_sha=git_sha,
            started_at=started_at,
            finished_at=finished_at,
            dry_run=dry_run,
            metrics=result.metrics,
            outcome=outcome,
            evaluation=evaluation,
            next_action=next_action,
        )

        dump_yaml(run_dir / "config.resolved.yaml", experiment.to_dict())
        dump_json(
            run_dir / "manifest.json",
            {
                "run_id": run_id,
                "experiment_id": experiment.id,
                "hypothesis_id": experiment.hypothesis_id,
                "kind": experiment.kind,
                "git_sha": git_sha,
                "dry_run": dry_run,
                "started_at": started_at,
                "finished_at": finished_at,
            },
        )
        dump_json(run_dir / "metrics.json", result.metrics)
        dump_json(run_dir / "decision.json", artifact.to_dict())
        (run_dir / "logs.txt").write_text("\n".join([*prep_logs, *result.logs]) + "\n", encoding="utf-8")

        updated = replace(experiment, status="completed")
        self.ledger.save_experiment(updated)

        return artifact

    def _git_sha(self) -> str:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                check=True,
                capture_output=True,
                text=True,
            )
            return proc.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"
