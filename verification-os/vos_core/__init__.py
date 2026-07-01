"""VerificationOS core — hypothesis ledger and experiment lifecycle."""

from vos_core.models import DecisionRecord, Experiment, Hypothesis, RunArtifact
from vos_core.ledger import Ledger
from vos_core.validate import validate_experiment, validate_hypothesis

__all__ = [
    "DecisionRecord",
    "Experiment",
    "Hypothesis",
    "RunArtifact",
    "Ledger",
    "validate_experiment",
    "validate_hypothesis",
]

def __getattr__(name: str):
    if name == "ExperimentRunner":
        from vos_core.experiment_runner import ExperimentRunner

        return ExperimentRunner
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
