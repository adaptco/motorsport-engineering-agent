import { get, post } from "../lib/api.js";
import { mountBranchScatter } from "../components/branch-scatter.js";
import { solverStatus } from "../components/solver-status.js";
import { esc, formatNumber } from "../lib/utils.js";

const sourceKinds = [
  "photo",
  "cad",
  "telemetry",
  "public_reference",
  "measurement",
  "wind_tunnel",
  "solver_case",
];

const sourceKindOptions = (selected = "photo") =>
  sourceKinds
    .map((kind) => `<option value="${kind}"${kind === selected ? " selected" : ""}>${kind.replaceAll("_", " ")}</option>`)
    .join("");

const sourceRow = (source = {}) => `
  <div class="form-grid full" data-source-row>
    <div class="field">
      <label>REFERENCE TYPE</label>
      <select data-source-kind>${sourceKindOptions(source.kind || "photo")}</select>
    </div>
    <div class="field">
      <label>LABEL</label>
      <input data-source-label value="${esc(source.label || "")}" placeholder="Front-view photo">
    </div>
    <div class="field full">
      <label>REFERENCE URI</label>
      <input data-source-uri value="${esc(source.uri || "")}" placeholder="s3://… or https://…">
    </div>
    <div class="actions full">
      <button type="button" class="button" data-remove-source>REMOVE REFERENCE</button>
    </div>
  </div>`;

const adjustmentRow = () => `
  <div class="form-grid full" data-adjustment-row>
    <div class="field"><label>ADJUSTMENT</label><input data-adjustment-key placeholder="rear_wing_angle_deg"></div>
    <div class="field"><label>VALUE</label><input data-adjustment-value placeholder="2.5 or JSON"></div>
    <div class="actions full"><button type="button" class="button" data-remove-adjustment>REMOVE ADJUSTMENT</button></div>
  </div>`;

const optionalNumber = (value, label) => {
  const normalized = String(value || "").trim();
  if (!normalized) return null;
  const number = Number(normalized);
  if (!Number.isFinite(number)) throw new Error(`${label} must be a valid number.`);
  return number;
};

const displayValue = (value, digits = 3) =>
  value === null || value === undefined ? "—" : formatNumber(value, digits);

const parseAdjustmentValue = (value) => {
  const normalized = value.trim();
  if (!normalized) return "";
  try {
    return JSON.parse(normalized);
  } catch {
    const number = Number(normalized);
    return Number.isFinite(number) ? number : normalized;
  }
};

const collectSourceRefs = (form) => {
  const refs = [];
  form.querySelectorAll("[data-source-row]").forEach((row) => {
    const uri = row.querySelector("[data-source-uri]").value.trim();
    const label = row.querySelector("[data-source-label]").value.trim();
    if (!uri && !label) return;
    if (!uri) throw new Error("Every labeled source reference requires a URI.");
    refs.push({
      kind: row.querySelector("[data-source-kind]").value,
      uri,
      ...(label ? { label } : {}),
    });
  });
  return refs;
};

const collectAdjustments = (form) => {
  const adjustments = {};
  form.querySelectorAll("[data-adjustment-row]").forEach((row) => {
    const key = row.querySelector("[data-adjustment-key]").value.trim();
    const value = row.querySelector("[data-adjustment-value]").value;
    if (!key && !value.trim()) return;
    if (!key) throw new Error("Every adjustment value requires an adjustment name.");
    adjustments[key] = parseAdjustmentValue(value);
  });
  return adjustments;
};

const renderError = (container, error) => {
  container.querySelector(".form-error")?.remove();
  container.insertAdjacentHTML(
    "afterbegin",
    `<div class="notice form-error">${esc(error?.message || String(error))}</div>`,
  );
};

export async function render(mount) {
  mount.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">AERO SIMULATION STUDIO</h1>
        <div class="page-subtitle">Durable simulation runs, provenance-linked inputs, and reviewable design branches.</div>
      </div>
      <button class="button button--primary" id="new-run">⊕ NEW RUN</button>
    </div>
    <div class="split">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">SIMULATION RUNS</span></div>
        <div id="aero-runs" class="list"></div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">BRANCH COMPARISON · CL vs CD</span></div>
        <div class="panel-body"><div id="aero-scatter" class="chart-container"></div></div>
      </section>
    </div>
    <div class="split" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">SOLVER STATE</span></div>
        <div class="panel-body" id="solver"><div class="empty">Select a run.</div></div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">RUN CONTEXT</span></div>
        <div class="panel-body" id="run-context"><div class="empty">Select a run.</div></div>
      </section>
    </div>
    <section class="panel" style="margin-top:12px">
      <div class="panel-header">
        <span class="panel-title">DESIGN BRANCHES</span>
        <button class="button button--primary" id="new-branch" disabled>⊕ PROPOSE BRANCH</button>
      </div>
      <div class="panel-body" id="branch-detail"><div class="empty">Select a run to review or propose branches.</div></div>
    </section>
    <div id="workflow-modal" hidden></div>`;

  let chart = null;
  let selectedRunId = null;
  let selectedBranchId = null;
  let latestState = null;

  const runsElement = document.getElementById("aero-runs");
  const solverElement = document.getElementById("solver");
  const contextElement = document.getElementById("run-context");
  const branchElement = document.getElementById("branch-detail");
  const branchButton = document.getElementById("new-branch");
  const modal = document.getElementById("workflow-modal");

  const renderRuns = (runs) => {
    runsElement.innerHTML = runs.length
      ? runs
          .map(
            (run) => `
              <button class="list-row" data-run="${esc(run.simulation_run_id)}" style="text-align:left;background:none;color:inherit;border:0">
                <div class="list-main">
                  <div class="list-title">${esc(run.vehicle_program_id || run.simulation_run_id)}</div>
                  <div class="list-meta">${esc(run.lifecycle_state)} · ${esc(run.updated_at || "")}</div>
                </div>
                <span class="tag">${esc(run.simulation_run_id.slice(0, 8))}</span>
              </button>`,
          )
          .join("")
      : '<div class="empty">No simulation runs. Create a run to establish an auditable aerodynamic baseline.</div>';
  };

  const renderState = (state) => {
    latestState = state;
    branchButton.disabled = false;
    solverElement.innerHTML = solverStatus(state);

    const identity = state.vehicle_snapshot?.identity || {};
    const geometry = state.geometry_state || {};
    const telemetryCount = (state.telemetry_links || []).length;
    const provenanceCount = (state.provenance || []).length;
    contextElement.innerHTML = `
      <div class="stack">
        <div><span class="tag">${esc(state.lifecycle_state)}</span></div>
        <div class="split">
          <div><div class="metric-label">VEHICLE</div><div class="small">${esc([identity.make, identity.model].filter(Boolean).join(" ") || "—")}</div></div>
          <div><div class="metric-label">GEOMETRY</div><div class="small">${esc(geometry.baseline_strategy || "—")}</div></div>
        </div>
        <div class="split">
          <div><div class="metric-label">SOURCES</div><div class="metric-value">${provenanceCount}</div></div>
          <div><div class="metric-label">TELEMETRY LINKS</div><div class="metric-value">${telemetryCount}</div></div>
        </div>
        <div><div class="metric-label">STATE HASH</div><div class="small">${esc((state.state_hash || "").slice(0, 18))}…</div></div>
      </div>`;

    const points = (state.branches || []).map((branch, index) => ({
      x: Number(branch.expected_delta_cd ?? 0),
      y: Number(branch.expected_delta_cl ?? 0),
      label: branch.branch_name || `B${index + 1}`,
    }));
    chart?.destroy?.();
    chart = mountBranchScatter(document.getElementById("aero-scatter"), points);

    const branches = state.branches || [];
    if (selectedBranchId && !branches.some((branch) => branch.branch_id === selectedBranchId)) {
      selectedBranchId = null;
    }
    const selectedBranch = branches.find((branch) => branch.branch_id === selectedBranchId) || branches.at(-1);
    selectedBranchId = selectedBranch?.branch_id || null;

    branchElement.innerHTML = branches.length
      ? `
        <div class="stack">
          <div class="list" id="branch-list">
            ${branches
              .map(
                (branch) => `
                  <button class="list-row" data-branch="${esc(branch.branch_id)}" style="text-align:left;background:none;color:inherit;border:0">
                    <div class="list-main"><div class="list-title">${esc(branch.branch_name)}</div><div class="list-meta">${esc(branch.change_mode)} · ${esc(branch.status)}</div></div>
                    <span class="tag">${esc(branch.branch_id.slice(0, 8))}</span>
                  </button>`,
              )
              .join("")}
          </div>
          <div id="selected-branch"></div>
        </div>`
      : '<div class="empty">No branches proposed. Use “Propose Branch” to create a traceable design hypothesis.</div>';

    const selectedBranchElement = document.getElementById("selected-branch");
    if (selectedBranchElement && selectedBranch) {
      const adjustments = Object.entries(selectedBranch.requested_adjustments || {});
      selectedBranchElement.innerHTML = `
        <div class="stack">
          <span class="tag">${esc(selectedBranch.branch_name)}</span>
          <div class="split">
            <div><div class="metric-label">EXPECTED ΔCL</div><div class="metric-value">${displayValue(selectedBranch.expected_delta_cl)}</div></div>
            <div><div class="metric-label">EXPECTED ΔCD</div><div class="metric-value">${displayValue(selectedBranch.expected_delta_cd)}</div></div>
          </div>
          <div><div class="metric-label">CHANGE SUMMARY</div><div class="small">${esc(selectedBranch.change_summary || "—")}</div></div>
          <div><div class="metric-label">REQUESTED ADJUSTMENTS</div><div class="small">${esc(adjustments.length ? adjustments.map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join(" · ") : "None recorded")}</div></div>
        </div>`;
    }
  };

  const selectRun = async (runId) => {
    try {
      selectedRunId = runId;
      const state = await get(`/aero/runs/${encodeURIComponent(runId)}`);
      renderState(state);
    } catch (error) {
      branchButton.disabled = true;
      branchElement.innerHTML = `<div class="notice">${esc(error.message)}</div>`;
      contextElement.innerHTML = `<div class="notice">${esc(error.message)}</div>`;
    }
  };

  const loadRuns = async () => {
    try {
      const runs = await get("/aero/runs");
      renderRuns(runs);
    } catch (error) {
      runsElement.innerHTML = `<div class="empty">${esc(error.message)}</div>`;
    }
  };

  const closeModal = () => {
    modal.hidden = true;
    modal.innerHTML = "";
  };

  const openRunModal = () => {
    modal.hidden = false;
    modal.innerHTML = `
      <div class="panel" style="margin-top:12px">
        <div class="panel-header"><span class="panel-title">NEW SIMULATION RUN</span></div>
        <div class="panel-body">
          <form id="new-run-form" class="form-grid">
            <div class="field"><label>PROJECT</label><input name="project" value="mea-demo" required></div>
            <div class="field"><label>PROGRAM</label><input name="program" value="gt4" required></div>
            <div class="field"><label>MAKE</label><input name="make" value="Aston Martin" required></div>
            <div class="field"><label>MODEL</label><input name="model" value="GT4" required></div>
            <div class="field"><label>YEAR</label><input name="year" type="number" value="2026"></div>
            <div class="field"><label>CLASS</label><input name="vehicleClass" value="GT4"></div>
            <div class="field"><label>TRIM</label><input name="trim" placeholder="Evo"></div>
            <div class="field"><label>CHASSIS CODE</label><input name="chassisCode" placeholder="V8 Vantage"></div>
            <div class="field full"><label>OBJECTIVE</label><textarea name="objective" required>Baseline aerodynamic correlation and branch comparison</textarea></div>
            <div class="field full"><label>GEOMETRY STRATEGY</label><select name="strategy"><option>proxy_geometry</option><option>public_cad</option><option>imported_cad</option><option>manual_sketch</option></select></div>
            <div class="field full"><label>PROVENANCE & INPUT REFERENCES</label><div id="source-rows" class="stack">${sourceRow()}</div><button type="button" class="button" id="add-source">ADD REFERENCE</button></div>
            <div class="actions full"><button type="button" class="button" id="close-run">CANCEL</button><button class="button button--primary">CREATE DURABLE RUN</button></div>
          </form>
        </div>
      </div>`;

    const form = document.getElementById("new-run-form");
    document.getElementById("close-run").onclick = closeModal;
    document.getElementById("add-source").onclick = () => {
      document.getElementById("source-rows").insertAdjacentHTML("beforeend", sourceRow());
    };
    document.getElementById("source-rows").addEventListener("click", (event) => {
      if (event.target.closest("[data-remove-source]")) event.target.closest("[data-source-row]").remove();
    });
    form.onsubmit = async (event) => {
      event.preventDefault();
      try {
        const data = new FormData(form);
        const sourceRefs = collectSourceRefs(form);
        const created = await post("/aero/runs", {
          project_id: data.get("project").trim(),
          vehicle_program_id: data.get("program").trim(),
          vehicle_identity: {
            make: data.get("make").trim(),
            model: data.get("model").trim(),
            year: optionalNumber(data.get("year"), "Year"),
            vehicle_class: data.get("vehicleClass").trim() || null,
            trim: data.get("trim").trim() || null,
            chassis_code: data.get("chassisCode").trim() || null,
          },
          source_refs: sourceRefs,
          simulation_objective: data.get("objective").trim(),
          baseline_geometry_strategy: data.get("strategy"),
          metadata: { created_via: "aero-studio", source_reference_count: sourceRefs.length },
        });
        closeModal();
        await loadRuns();
        await selectRun(created.simulation_run_id);
      } catch (error) {
        renderError(form, error);
      }
    };
  };

  const openBranchModal = () => {
    if (!selectedRunId || !latestState) return;
    modal.hidden = false;
    modal.innerHTML = `
      <div class="panel" style="margin-top:12px">
        <div class="panel-header"><span class="panel-title">PROPOSE DESIGN BRANCH</span></div>
        <div class="panel-body">
          <form id="new-branch-form" class="form-grid">
            <div class="field"><label>BRANCH NAME</label><input name="branchName" placeholder="rear-wing-plus-2-deg" required></div>
            <div class="field"><label>CHANGE MODE</label><select name="changeMode"><option value="geometry">geometry</option><option value="setup">setup</option><option value="solver">solver</option><option value="boundary_condition">boundary condition</option></select></div>
            <div class="field"><label>EXPECTED ΔCL</label><input name="deltaCl" type="number" step="any" placeholder="0.015"></div>
            <div class="field"><label>EXPECTED ΔCD</label><input name="deltaCd" type="number" step="any" placeholder="0.003"></div>
            <div class="field full"><label>CHANGE SUMMARY</label><textarea name="summary" placeholder="Describe the hypothesis and expected trade-off." required></textarea></div>
            <div class="field full"><label>REQUESTED ADJUSTMENTS</label><div id="adjustment-rows" class="stack">${adjustmentRow()}</div><button type="button" class="button" id="add-adjustment">ADD ADJUSTMENT</button></div>
            <div class="actions full"><button type="button" class="button" id="close-branch">CANCEL</button><button class="button button--primary">SUBMIT PROPOSAL</button></div>
          </form>
        </div>
      </div>`;

    const form = document.getElementById("new-branch-form");
    document.getElementById("close-branch").onclick = closeModal;
    document.getElementById("add-adjustment").onclick = () => {
      document.getElementById("adjustment-rows").insertAdjacentHTML("beforeend", adjustmentRow());
    };
    document.getElementById("adjustment-rows").addEventListener("click", (event) => {
      if (event.target.closest("[data-remove-adjustment]")) event.target.closest("[data-adjustment-row]").remove();
    });
    form.onsubmit = async (event) => {
      event.preventDefault();
      try {
        const data = new FormData(form);
        const updated = await post(`/aero/runs/${encodeURIComponent(selectedRunId)}/branches`, {
          branch_name: data.get("branchName").trim(),
          change_mode: data.get("changeMode"),
          change_summary: data.get("summary").trim(),
          requested_adjustments: collectAdjustments(form),
          expected_delta_cl: optionalNumber(data.get("deltaCl"), "Expected ΔCL"),
          expected_delta_cd: optionalNumber(data.get("deltaCd"), "Expected ΔCD"),
          metadata: { created_via: "aero-studio", source_state_hash: latestState.state_hash },
        });
        selectedBranchId = updated.branches?.at(-1)?.branch_id || null;
        closeModal();
        await loadRuns();
        renderState(updated);
      } catch (error) {
        renderError(form, error);
      }
    };
  };

  runsElement.addEventListener("click", (event) => {
    const button = event.target.closest("[data-run]");
    if (button) selectRun(button.dataset.run);
  });
  branchElement.addEventListener("click", (event) => {
    const button = event.target.closest("[data-branch]");
    if (!button || !latestState) return;
    selectedBranchId = button.dataset.branch;
    renderState(latestState);
  });
  document.getElementById("new-run").onclick = openRunModal;
  branchButton.onclick = openBranchModal;

  await loadRuns();
}
