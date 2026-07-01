#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vos_core.experiment_runner import ExperimentRunner
from vos_core.ledger import Ledger
from vos_core.models import DecisionRecord, Experiment, Hypothesis
from vos_core.validate import dump_yaml, load_yaml


ROOT = Path(__file__).resolve().parent


def cmd_status(_: argparse.Namespace) -> int:
    ledger = Ledger(ROOT)
    summary = ledger.status_summary()
    print(json.dumps(summary, indent=2))
    print("\nHypotheses:")
    for h in ledger.list_hypotheses():
        print(f"  {h.id} [{h.status}] {h.title} ({h.hypothesis_class})")
    print("\nExperiments:")
    for e in ledger.list_experiments():
        print(f"  {e.id} [{e.status}] {e.kind} -> {e.hypothesis_id}")
    return 0


def cmd_hypothesis_init(args: argparse.Namespace) -> int:
    ledger = Ledger(ROOT)
    template_path = Path(args.from_template)
    data = load_yaml(template_path)
    if args.id:
        data["id"] = args.id
    else:
        data["id"] = ledger.next_hypothesis_id()
    hypothesis = Hypothesis.from_dict(data)
    path = ledger.save_hypothesis(hypothesis)
    print(f"Created hypothesis {hypothesis.id} at {path}")
    return 0


def cmd_experiment_init(args: argparse.Namespace) -> int:
    ledger = Ledger(ROOT)
    template_path = Path(args.from_template)
    data = load_yaml(template_path)
    data["id"] = ledger.next_experiment_id()
    data["kind"] = args.kind
    if args.hypothesis:
        data["hypothesis_id"] = args.hypothesis
    experiment = Experiment.from_dict(data)
    path = ledger.save_experiment(experiment)
    print(f"Created experiment {experiment.id} at {path}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    runner = ExperimentRunner(ROOT)
    artifact = runner.run(Path(args.experiment), dry_run=args.dry_run)
    print(json.dumps(artifact.to_dict(), indent=2))
    print(f"\nOutcome: {artifact.outcome}")
    print(f"Next: {artifact.next_action}")
    return 0 if artifact.outcome == "pass" else 1


def cmd_decision_record(args: argparse.Namespace) -> int:
    ledger = Ledger(ROOT)
    record = DecisionRecord(
        hypothesis_id=args.hypothesis,
        outcome=args.outcome,
        memo=args.memo,
        recorded_at=Ledger.utc_now(),
        experiment_id=args.experiment or "",
        run_id=args.run or "",
    )
    path = ledger.record_decision(record)
    print(f"Recorded decision at {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vos", description="VerificationOS CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show ledger summary")
    status.set_defaults(func=cmd_status)

    hyp = sub.add_parser("hypothesis", help="Hypothesis commands")
    hyp_sub = hyp.add_subparsers(dest="hypothesis_command", required=True)
    hyp_init = hyp_sub.add_parser("init", help="Create hypothesis from template")
    hyp_init.add_argument("--from", dest="from_template", default=str(ROOT / "templates/hypothesis.template.yaml"))
    hyp_init.add_argument("--id", default="")
    hyp_init.set_defaults(func=cmd_hypothesis_init)

    exp = sub.add_parser("experiment", help="Experiment commands")
    exp_sub = exp.add_subparsers(dest="experiment_command", required=True)
    exp_init = exp_sub.add_parser("init", help="Create experiment from template")
    exp_init.add_argument("--kind", required=True)
    exp_init.add_argument("--hypothesis", default="H-001")
    exp_init.add_argument("--from", dest="from_template", default=str(ROOT / "templates/experiment.template.yaml"))
    exp_init.set_defaults(func=cmd_experiment_init)

    run = sub.add_parser("run", help="Execute a preregistered experiment")
    run.add_argument("experiment", help="Path to experiment YAML")
    run.add_argument("--dry-run", action="store_true", help="Simulate without external systems")
    run.set_defaults(func=cmd_run)

    decision = sub.add_parser("decision", help="Decision commands")
    decision_sub = decision.add_subparsers(dest="decision_command", required=True)
    decision_record = decision_sub.add_parser("record", help="Record kill/pivot/escalate memo")
    decision_record.add_argument("--hypothesis", required=True)
    decision_record.add_argument("--outcome", required=True, choices=["kill", "pivot", "escalate", "promote"])
    decision_record.add_argument("--memo", required=True)
    decision_record.add_argument("--experiment", default="")
    decision_record.add_argument("--run", default="")
    decision_record.set_defaults(func=cmd_decision_record)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.func(args)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()
