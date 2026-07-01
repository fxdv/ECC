from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from vos_core.models import DecisionRecord, Experiment, Hypothesis


ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_hypothesis(data: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(_load_schema("hypothesis.schema.json"))
    return sorted({f"{'.'.join(str(p) for p in err.path)}: {err.message}" for err in validator.iter_errors(data)})


def validate_experiment(data: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(_load_schema("experiment.schema.json"))
    return sorted({f"{'.'.join(str(p) for p in err.path)}: {err.message}" for err in validator.iter_errors(data)})


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
