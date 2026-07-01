const state = { snapshot: null };

const els = {
  generatedAt: document.getElementById("generated-at"),
  summaryCards: document.getElementById("summary-cards"),
  pipelines: document.getElementById("pipelines"),
  runsTable: document.getElementById("runs-table"),
  hypothesisList: document.getElementById("hypothesis-list"),
  decisionList: document.getElementById("decision-list"),
  quickExperiment: document.getElementById("quick-experiment"),
  quickDryRun: document.getElementById("quick-dry-run"),
  quickRunForm: document.getElementById("quick-run-form"),
  quickRunResult: document.getElementById("quick-run-result"),
  refreshBtn: document.getElementById("refresh-btn"),
  runModal: document.getElementById("run-modal"),
  modalTitle: document.getElementById("modal-title"),
  modalBody: document.getElementById("modal-body"),
  modalClose: document.getElementById("modal-close"),
};

function badge(text, kind = "neutral") {
  return `<span class="badge ${kind}">${text}</span>`;
}

function outcomeKind(outcome) {
  if (outcome === "pass") return "pass";
  if (outcome === "fail") return "fail";
  if (outcome === "ambiguous") return "ambiguous";
  return "neutral";
}

function fmtTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

function renderSummary(summary) {
  const cards = [
    ["Hypotheses", summary.hypotheses.total, `${summary.hypotheses.active} active`],
    ["Experiments", summary.experiments.total, `${summary.experiments.completed} completed`],
    ["Runs", summary.runs.total, `${summary.runs.pass} pass / ${summary.runs.fail} fail`],
    ["Decisions", summary.decisions, "Recorded memos"],
  ];
  els.summaryCards.innerHTML = cards
    .map(
      ([label, value, sub]) => `
      <article class="metric-card">
        <div class="label">${label}</div>
        <div class="value">${value}</div>
        <div class="sub">${sub}</div>
      </article>`
    )
    .join("");
}

function renderPipelines(pipelines) {
  if (!pipelines.length) {
    els.pipelines.innerHTML = `<div class="empty">No pipelines yet. Generate a harness chain with <code>vos harness chain</code>.</div>`;
    return;
  }

  els.pipelines.innerHTML = pipelines
    .map((pipeline) => {
      const steps = pipeline.experiments
        .map((exp) => {
          const latest = exp.latest_run;
          const outcome = latest?.outcome;
          const outcomeBadge = latest
            ? badge(outcome, outcomeKind(outcome))
            : badge(exp.status, exp.status === "completed" ? "pass" : "neutral");
          return `
            <div class="step">
              <div class="kind">${exp.kind}</div>
              <div class="title">${exp.id} — ${exp.title}</div>
              <div class="meta">
                ${outcomeBadge}
                ${exp.depends_on?.length ? badge(`deps: ${exp.depends_on.join(", ")}`, "neutral") : ""}
              </div>
            </div>`;
        })
        .join("");

      return `
        <article class="pipeline-card">
          <div class="pipeline-title">
            <h3>${pipeline.hypothesis_id} — ${pipeline.title}</h3>
            ${badge(pipeline.status, pipeline.status === "active" ? "active" : "neutral")}
          </div>
          <div class="pipeline-steps">${steps}</div>
        </article>`;
    })
    .join("");
}

function renderRuns(runs) {
  if (!runs.length) {
    els.runsTable.innerHTML = `<tr><td colspan="6" class="empty">No runs yet.</td></tr>`;
    return;
  }

  els.runsTable.innerHTML = runs
    .map(
      (run) => `
      <tr>
        <td><code>${run.run_id}</code></td>
        <td>${run.experiment_id || "—"}</td>
        <td>${run.kind || "—"}</td>
        <td>${badge(run.outcome || "unknown", outcomeKind(run.outcome))}</td>
        <td>${fmtTime(run.started_at)}</td>
        <td><button class="btn btn-sm" data-run="${run.run_id}">View</button></td>
      </tr>`
    )
    .join("");

  els.runsTable.querySelectorAll("[data-run]").forEach((btn) => {
    btn.addEventListener("click", () => openRunModal(btn.dataset.run));
  });
}

function renderHypotheses(hypotheses) {
  els.hypothesisList.innerHTML = hypotheses.length
    ? hypotheses
        .map(
          (h) => `
        <div class="stack-item">
          <div class="title">${h.id}</div>
          <div class="meta">${h.title}</div>
          <div class="meta">${badge(h.hypothesis_class, "neutral")} ${badge(h.status, h.status === "active" ? "active" : "neutral")}</div>
        </div>`
        )
        .join("")
    : `<div class="empty">No hypotheses registered.</div>`;
}

function renderDecisions(decisions) {
  els.decisionList.innerHTML = decisions.length
    ? decisions
        .map(
          (d) => `
        <div class="stack-item">
          <div class="title">${d.hypothesis_id} → ${d.outcome}</div>
          <div class="meta">${d.memo}</div>
          <div class="meta">${fmtTime(d.recorded_at)}</div>
        </div>`
        )
        .join("")
    : `<div class="empty">No decisions recorded.</div>`;
}

function renderQuickRunOptions(experiments) {
  els.quickExperiment.innerHTML = experiments
    .map((e) => `<option value="${e.id}">${e.id} — ${e.kind}</option>`)
    .join("");
}

async function loadDashboard() {
  const res = await fetch("/api/overview");
  const snapshot = await res.json();
  state.snapshot = snapshot;

  els.generatedAt.textContent = `Updated ${fmtTime(snapshot.generated_at)}`;
  renderSummary(snapshot.summary);
  renderPipelines(snapshot.pipelines);
  renderRuns(snapshot.recent_runs);
  renderHypotheses(snapshot.hypotheses);
  renderDecisions(snapshot.recent_decisions);
  renderQuickRunOptions(snapshot.experiments);
}

async function openRunModal(runId) {
  const res = await fetch(`/api/runs/${runId}`);
  const data = await res.json();
  els.modalTitle.textContent = `Run ${runId}`;
  els.modalBody.innerHTML = `
    <p>${badge(data.outcome, outcomeKind(data.outcome))} ${data.kind || ""} · ${data.experiment_id || ""}</p>
    <p><strong>Next action:</strong> ${data.next_action || "—"}</p>
    <h4>Metrics</h4>
    <pre>${JSON.stringify(data.metrics || {}, null, 2)}</pre>
    <h4>Evaluation</h4>
    <pre>${JSON.stringify(data.evaluation || {}, null, 2)}</pre>
    <h4>Logs</h4>
    <pre>${(data.logs || []).join("\n")}</pre>
  `;
  els.runModal.showModal();
}

els.refreshBtn.addEventListener("click", loadDashboard);
els.modalClose.addEventListener("click", () => els.runModal.close());

els.quickRunForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const experimentId = els.quickExperiment.value;
  const dryRun = els.quickDryRun.checked;
  els.quickRunResult.classList.remove("hidden");
  els.quickRunResult.textContent = "Running...";

  const res = await fetch(`/api/experiments/${experimentId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: dryRun }),
  });
  const payload = await res.json();
  els.quickRunResult.textContent = JSON.stringify(payload, null, 2);
  await loadDashboard();
});

loadDashboard().catch((err) => {
  els.summaryCards.innerHTML = `<div class="empty">Failed to load dashboard: ${err.message}</div>`;
});
