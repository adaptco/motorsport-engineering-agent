import { get, upload } from "../lib/api.js";
import { startPolling } from "../lib/polling.js";
import { metricCard } from "../components/metric-card.js";
import { evidenceFeed } from "../components/evidence-feed.js";
import { recommendationCard } from "../components/recommendation-card.js";
import { timeline } from "../components/timeline.js";
import { esc } from "../lib/utils.js";

const jsonBlock = (value) => `<pre class="json-block">${esc(JSON.stringify(value, null, 2))}</pre>`;

const renderNotice = (element, message) => {
  element.innerHTML = `<div class="notice">${esc(message)}</div>`;
};

const renderSessionList = (sessions) => {
  if (!sessions.length) {
    return '<div class="empty">No runtime logs have been parsed yet.</div>';
  }
  return sessions
    .map(
      (session) => `
        <button class="list-row mission-control-session" data-session-id="${esc(session.session_id)}" type="button">
          <div class="list-main">
            <div class="list-title">${esc(session.filename)}</div>
            <div class="list-meta">${esc(session.session_id)} · ${session.rows} rows · ${esc(
              (session.columns || []).slice(0, 4).join(", "),
            )}</div>
          </div>
          <span class="tag">REVIEW</span>
        </button>`,
    )
    .join("");
};

const renderRouteTable = (routes) => {
  if (!routes.length) {
    return '<div class="empty">No routes returned by the control plane.</div>';
  }
  return `
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr><th>METHOD</th><th>PATH</th></tr></thead>
        <tbody>${routes
          .map(
            (route) => `<tr><td><span class="tag">${esc(route.method)}</span></td><td><code>${esc(route.path)}</code></td></tr>`,
          )
          .join("")}</tbody>
      </table>
    </div>`;
};

export async function render(mount) {
  mount.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">MISSION CONTROL</h1>
        <div class="page-subtitle">System state, runtime-log review, API discovery, and bounded operator inspection.</div>
      </div>
      <button id="mc-refresh" class="button" type="button">REFRESH</button>
    </div>
    <div id="mc-metrics" class="grid grid-4"></div>
    <div class="grid grid-2" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">SESSION TIMELINE</span></div>
        <div class="panel-body" id="mc-timeline"></div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">DATA SOURCES</span></div>
        <div class="panel-body" id="mc-sources"></div>
      </section>
    </div>
    <div class="grid grid-2" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">RUNTIME LOG INTAKE</span></div>
        <div class="panel-body stack">
          <div class="field">
            <label for="mc-log-file">CSV OR TXT RUNTIME LOG</label>
            <input id="mc-log-file" type="file" accept=".csv,.txt,text/csv,text/plain">
          </div>
          <div class="actions"><button id="mc-upload-log" class="button button--primary" type="button">PARSE LOG</button></div>
          <div id="mc-upload-result" class="small">Files are parsed through the existing runtime-log API and remain available for review.</div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">RUNTIME SESSIONS</span></div>
        <div class="panel-body list" id="mc-session-list"></div>
      </section>
    </div>
    <div class="grid grid-2" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">SESSION DEBRIEF</span></div>
        <div class="panel-body" id="mc-session-detail"><div class="empty">Select a runtime session to inspect its debrief and parsed payload.</div></div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">RUNTIME STATE INSPECTOR</span></div>
        <div class="panel-body stack">
          <div class="form-grid">
            <div class="field"><label for="mc-state-session">SESSION ID</label><input id="mc-state-session" value="default" placeholder="session-id"></div>
            <div class="actions"><button id="mc-load-state" class="button" type="button">LOAD SNAPSHOT</button></div>
          </div>
          <div id="mc-state-detail" class="small">Read-only inspection; state mutations remain behind the established authenticated API.</div>
        </div>
      </section>
    </div>
    <div class="grid grid-2" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">JOB STATUS INSPECTOR</span></div>
        <div class="panel-body stack">
          <div class="form-grid">
            <div class="field"><label for="mc-job-id">JOB ID</label><input id="mc-job-id" placeholder="job-id"></div>
            <div class="actions"><button id="mc-load-job" class="button" type="button">FETCH JOB</button></div>
          </div>
          <div id="mc-job-detail" class="small">Read-only lookup. CI-fix submission remains outside this bounded operator panel.</div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">API SURFACE</span><button id="mc-load-routes" class="button" type="button">DISCOVER</button></div>
        <div class="panel-body" id="mc-route-detail"><div class="empty">Discover the currently mounted control-plane routes.</div></div>
      </section>
    </div>
    <div class="split" style="margin-top:12px">
      <section class="panel">
        <div class="panel-header"><span class="panel-title">EVIDENCE FEED</span></div>
        <div id="mc-evidence"></div>
      </section>
      <section class="panel">
        <div class="panel-header"><span class="panel-title">RECOMMENDATION QUEUE</span></div>
        <div id="mc-recs" class="stack" style="padding:12px"></div>
      </section>
    </div>`;

  const metricsElement = document.getElementById("mc-metrics");
  const timelineElement = document.getElementById("mc-timeline");
  const sourcesElement = document.getElementById("mc-sources");
  const sessionListElement = document.getElementById("mc-session-list");
  const sessionDetailElement = document.getElementById("mc-session-detail");
  const uploadResultElement = document.getElementById("mc-upload-result");
  const stateDetailElement = document.getElementById("mc-state-detail");
  const jobDetailElement = document.getElementById("mc-job-detail");
  const routeDetailElement = document.getElementById("mc-route-detail");

  const loadSession = async (sessionId) => {
    try {
      sessionDetailElement.innerHTML = '<div class="small">Loading session debrief…</div>';
      const [session, debrief] = await Promise.all([
        get(`/runtime/sessions/${encodeURIComponent(sessionId)}`),
        get(`/runtime/sessions/${encodeURIComponent(sessionId)}/debrief`),
      ]);
      sessionDetailElement.innerHTML = `
        <div class="stack">
          <div><span class="tag">${esc(session.session_id)}</span></div>
          <div class="split">
            <div><div class="metric-label">ROWS</div><div class="metric-value">${session.rows}</div></div>
            <div><div class="metric-label">COLUMNS</div><div class="metric-value">${(session.columns || []).length}</div></div>
          </div>
          <div><div class="metric-label">DEBRIEF</div><div class="small">${esc(debrief.headline || "—")}</div></div>
          <div><div class="metric-label">OBSERVATIONS</div><div class="small">${esc((debrief.observations || []).join(" · ") || "—")}</div></div>
          <details><summary class="small">VIEW PARSED PAYLOAD</summary>${jsonBlock(session)}</details>
        </div>`;
    } catch (error) {
      renderNotice(sessionDetailElement, error.message);
    }
  };

  const loadRuntimeState = async () => {
    const sessionId = document.getElementById("mc-state-session").value.trim() || "default";
    try {
      stateDetailElement.innerHTML = '<div class="small">Loading runtime state…</div>';
      const [snapshot, events] = await Promise.all([
        get(`/runtime-state/snapshot?session_id=${encodeURIComponent(sessionId)}`),
        get(`/runtime-state/events?session_id=${encodeURIComponent(sessionId)}`),
      ]);
      stateDetailElement.innerHTML = `
        <div class="stack">
          <div class="split">
            <div><div class="metric-label">EVENTS</div><div class="metric-value">${(events.events || []).length}</div></div>
            <div><div class="metric-label">LAST SEQUENCE</div><div class="metric-value">${snapshot.last_seq ?? "—"}</div></div>
          </div>
          <details><summary class="small">VIEW SNAPSHOT</summary>${jsonBlock(snapshot)}</details>
        </div>`;
    } catch (error) {
      renderNotice(stateDetailElement, `Runtime state is unavailable for this session: ${error.message}`);
    }
  };

  const loadJob = async () => {
    const jobId = document.getElementById("mc-job-id").value.trim();
    if (!jobId) {
      renderNotice(jobDetailElement, "Enter a job ID before requesting status.");
      return;
    }
    try {
      jobDetailElement.innerHTML = '<div class="small">Loading job status…</div>';
      const job = await get(`/jobs/${encodeURIComponent(jobId)}`);
      jobDetailElement.innerHTML = jsonBlock(job);
    } catch (error) {
      renderNotice(jobDetailElement, error.message);
    }
  };

  const loadRoutes = async () => {
    try {
      routeDetailElement.innerHTML = '<div class="small">Discovering API routes…</div>';
      const data = await get("/api/routes");
      routeDetailElement.innerHTML = renderRouteTable(data.routes || []);
    } catch (error) {
      renderNotice(routeDetailElement, error.message);
    }
  };

  const load = async () => {
    try {
      const [health, dependencies, sessions, sources] = await Promise.all([
        get("/healthz"),
        get("/healthz/dependencies"),
        get("/runtime/sessions"),
        get("/ingest/sources"),
      ]);
      metricsElement.innerHTML =
        metricCard("SESSIONS", sessions?.length ?? 0, "parsed") +
        metricCard("SOURCES", sources?.length ?? 0, "parsers") +
        metricCard("DB", dependencies?.db_pool?.status || "ok", "dependency") +
        metricCard("KERNEL", health?.kernel_version || "—", "version");
      timelineElement.innerHTML = timeline(
        (sessions || []).slice(-8).map((session, index) => ({
          label: `S${index + 1}`,
          meta: `${session.session_id} · ${session.rows} rows`,
        })),
      );
      sourcesElement.innerHTML =
        (sources || [])
          .map(
            (source) => `
              <div class="list-row">
                <span class="health-pill health-pill--${source.available ? "ok" : "bad"}">● ${source.available ? "READY" : "OFF"}</span>
                <div class="list-main"><div class="list-title">${esc(source.vendor)}</div><div class="list-meta">${esc(
                  (source.native_extensions || []).join(", "),
                )}</div></div>
              </div>`,
          )
          .join("") || '<div class="empty">No sources.</div>';
      sessionListElement.innerHTML = renderSessionList(sessions || []);
      document.getElementById("mc-evidence").innerHTML = evidenceFeed([]);
      document.getElementById("mc-recs").innerHTML = recommendationCard({
        priority: "INFO",
        action: "Evidence and recommendations are populated by session analysis.",
        trigger: "No current packets",
      });
    } catch (error) {
      renderNotice(metricsElement, `Backend unavailable: ${error.message}`);
    }
  };

  document.getElementById("mc-refresh").onclick = load;
  document.getElementById("mc-session-list").addEventListener("click", (event) => {
    const button = event.target.closest("[data-session-id]");
    if (button) loadSession(button.dataset.sessionId);
  });
  document.getElementById("mc-upload-log").onclick = async () => {
    const file = document.getElementById("mc-log-file").files?.[0];
    if (!file) {
      renderNotice(uploadResultElement, "Choose a CSV or TXT runtime log before parsing.");
      return;
    }
    try {
      uploadResultElement.innerHTML = '<div class="small">Parsing runtime log…</div>';
      const parsed = await upload("/runtime/logs/parse", file);
      uploadResultElement.innerHTML = `<div class="small">Parsed ${parsed.summary.rows} rows into session <strong>${esc(parsed.summary.session_id)}</strong>.</div>`;
      await load();
      await loadSession(parsed.summary.session_id);
    } catch (error) {
      renderNotice(uploadResultElement, error.message);
    }
  };
  document.getElementById("mc-load-state").onclick = loadRuntimeState;
  document.getElementById("mc-load-job").onclick = loadJob;
  document.getElementById("mc-load-routes").onclick = loadRoutes;

  startPolling("mc", load, 5000);
  await load();
}
