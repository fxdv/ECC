from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from vos_core.experiment_runner import ExperimentRunner
from vos_core.ledger import Ledger
from vos_core.models import DecisionRecord


def create_app(root: Path | None = None) -> FastAPI:
    root = root or Path(__file__).resolve().parent.parent
    ledger = Ledger(root)
    runner = ExperimentRunner(root)
    static_dir = Path(__file__).resolve().parent / "static"

    app = FastAPI(title="VerificationOS Dashboard", version="0.2.0")

    class RunRequest(BaseModel):
        dry_run: bool = True

    class DecisionRequest(BaseModel):
        hypothesis_id: str
        outcome: str = Field(pattern="^(kill|pivot|escalate|promote)$")
        memo: str
        experiment_id: str = ""
        run_id: str = ""

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/overview")
    def overview() -> dict:
        return ledger.dashboard_snapshot()

    @app.get("/api/hypotheses")
    def hypotheses() -> list[dict]:
        return [h.to_dict() for h in ledger.list_hypotheses()]

    @app.get("/api/hypotheses/{hypothesis_id}")
    def hypothesis_detail(hypothesis_id: str) -> dict:
        hypothesis = ledger.get_hypothesis(hypothesis_id)
        if hypothesis is None:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
        experiments = ledger.experiments_for_hypothesis(hypothesis_id)
        return {
            "hypothesis": hypothesis.to_dict(),
            "experiments": [e.to_dict() for e in experiments],
            "runs": [r for r in ledger.list_runs() if r.get("hypothesis_id") == hypothesis_id][:50],
        }

    @app.get("/api/experiments")
    def experiments() -> list[dict]:
        return [e.to_dict() for e in ledger.list_experiments()]

    @app.get("/api/experiments/{experiment_id}")
    def experiment_detail(experiment_id: str) -> dict:
        experiment = ledger.get_experiment(experiment_id)
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {
            "experiment": experiment.to_dict(),
            "latest_run": ledger.latest_run_for_experiment(experiment_id),
        }

    @app.post("/api/experiments/{experiment_id}/run")
    def run_experiment(experiment_id: str, body: RunRequest | None = None) -> dict:
        experiment = ledger.get_experiment(experiment_id)
        if experiment is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        path = ledger.experiments_dir / f"{experiment.id.lower()}.yaml"
        dry_run = body.dry_run if body is not None else True
        artifact = runner.run(path, dry_run=dry_run)
        return artifact.to_dict()

    @app.get("/api/runs")
    def runs() -> list[dict]:
        return ledger.list_runs()

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str) -> dict:
        payload = ledger.get_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return payload

    @app.get("/api/decisions")
    def decisions() -> list[dict]:
        return ledger.list_decisions()

    @app.post("/api/decisions")
    def record_decision(body: DecisionRequest) -> dict:
        record = DecisionRecord(
            hypothesis_id=body.hypothesis_id,
            outcome=body.outcome,
            memo=body.memo,
            recorded_at=Ledger.utc_now(),
            experiment_id=body.experiment_id,
            run_id=body.run_id,
        )
        path = ledger.record_decision(record)
        return {"path": str(path), "record": record.to_dict()}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app


app = create_app()
