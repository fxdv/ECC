from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.api import create_app
from harness.generator import HarnessGenerator, HarnessSpec
from harness.pipeline import HarnessPipeline
from vos_core.ledger import Ledger
from vos_core.models import Hypothesis


ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    for sub in ("data/hypotheses", "data/experiments", "data/runs", "data/decisions"):
        (tmp_path / sub).mkdir(parents=True)
    ledger = Ledger(tmp_path)
    ledger.save_hypothesis(
        Hypothesis.from_dict(
                {
                    "id": "H-900",
                    "title": "Temp thesis",
                    "segment": "test",
                    "hypothesis_class": "technical",
                    "claim": "Temporary claim for harness tests",
                    "pass_criteria": ["Pipeline completes"],
                    "kill_rules": ["stop"],
                    "status": "active",
                }
        )
    )
    return tmp_path


def test_harness_generator_creates_valid_experiment(temp_root: Path):
    generator = HarnessGenerator(temp_root)
    experiment = generator.generate_experiment(
        HarnessSpec(
            hypothesis_id="H-900",
            kind="benchmark_eval",
            claim="Candidate beats baseline on throughput",
        )
    )
    assert experiment.id == "E-001"
    assert experiment.kind == "benchmark_eval"
    assert (temp_root / "data/experiments/e-001.yaml").exists()


def test_harness_chain_links_dependencies(temp_root: Path):
    generator = HarnessGenerator(temp_root)
    created = generator.generate_chain("H-900", chain="optimization_wedge")
    assert len(created) == 2
    assert created[0].kind == "profiling"
    assert created[1].depends_on == [created[0].id]


def test_harness_pipeline_runs_in_order(temp_root: Path):
    generator = HarnessGenerator(temp_root)
    generator.generate_chain("H-900", chain="optimization_wedge", base_claim="Pipeline claim")

    pipeline = HarnessPipeline(temp_root)
    result = pipeline.run("H-900", dry_run=True)
    assert len(result.outcomes) == 2
    assert result.outcomes[0]["kind"] == "profiling"
    assert result.completed is True


def test_dashboard_overview_api(temp_root: Path):
    generator = HarnessGenerator(temp_root)
    generator.generate_experiment(
        HarnessSpec(hypothesis_id="H-900", kind="research_paper", claim="Paper claim")
    )

    client = TestClient(create_app(temp_root))
    response = client.get("/api/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["hypotheses"]["total"] == 1
    assert len(payload["experiments"]) == 1
    assert "pipelines" in payload


def test_dashboard_run_experiment_api(temp_root: Path):
    generator = HarnessGenerator(temp_root)
    experiment = generator.generate_experiment(
        HarnessSpec(hypothesis_id="H-900", kind="research_paper", claim="Runnable claim")
    )

    client = TestClient(create_app(temp_root))
    response = client.post(f"/api/experiments/{experiment.id}/run", json={"dry_run": True})
    assert response.status_code == 200
    assert response.json()["outcome"] == "pass"


def test_dashboard_index_served(temp_root: Path):
    client = TestClient(create_app(temp_root))
    response = client.get("/")
    assert response.status_code == 200
    assert "VerificationOS" in response.text
