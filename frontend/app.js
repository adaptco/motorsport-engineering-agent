const API_BASE = ''; // same-origin static serve

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

const state = {
  tab: 'dashboard',
  health: null,
  sessions: [],
  jobs: {},
  ingestSources: [],
  runtimeSnapshot: null,
  runtimeEvents: [],
  loading: new Set(),
};

function setTab(id) {
  state.tab = id;
  $$('nav button').forEach(b => b.classList.toggle('active', b.dataset.tab === id));
  $$('.tab-panel').forEach(p => p.classList.toggle('hidden', p.id !== `tab-${id}`));
  if (id === 'runtime') loadSessions();
  if (id === 'ingest') loadIngestSources();
  if (id === 'jobs') { /* jobs are loaded on demand */ }
  if (id === 'state') loadRuntimeState();
}

async function api(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, { headers: { 'Accept': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

function setLoading(key, yes) {
  yes ? state.loading.add(key) : state.loading.delete(key);
  const el = $(`[data-loading="${key}"]`);
  if (el) el.classList.toggle('hidden', !yes);
}

/* ---------- Dashboard ---------- */
async function loadHealth() {
  try {
    const [health, deps] = await Promise.all([api('/healthz'), api('/healthz/dependencies')]);
    state.health = { ...health, ...deps };
    renderHealth();
  } catch (e) {
    $('#health-grid').innerHTML = `<div class="panel"><span class="status-indicator status-err"></span> Control Plane unreachable: ${e.message}</div>`;
  }
}

function renderHealth() {
  const h = state.health || {};
  const ok = h.status === 'ok';
  $('#health-grid').innerHTML = `
    <div class="panel">
      <h2><span class="status-indicator ${ok ? 'status-ok' : 'status-err'}"></span>Control Plane</h2>
      <div>Version: <strong>${h.kernel_version || '—'}</strong></div>
      <div>Package: ${h.package_version || '—'}</div>
    </div>
    <div class="panel">
      <h2><span class="status-indicator ${h.db_pool?.status === 'ok' ? 'status-ok' : 'status-warn'}"></span>Database Pool</h2>
      <pre class="json">${JSON.stringify(h.db_pool || {}, null, 2)}</pre>
    </div>
    <div class="panel">
      <h2>Ledger Path</h2>
      <code>${h.session_ledger_db_path || '—'}</code>
    </div>
  `;
}

/* ---------- Runtime Logs ---------- */
async function loadSessions() {
  setLoading('sessions', true);
  try {
    state.sessions = await api('/runtime/sessions');
    renderSessions();
  } finally { setLoading('sessions', false); }
}

function renderSessions() {
  const rows = state.sessions.map(s => `
    <tr>
      <td><a href="#" onclick="viewSession('${s.session_id}');return false;">${s.session_id}</a></td>
      <td>${s.filename}</td>
      <td>${s.rows}</td>
      <td>${s.columns.join(', ')}</td>
    </tr>
  `).join('');
  $('#sessions-table tbody').innerHTML = rows || '<tr><td colspan="4">No sessions parsed yet.</td></tr>';
}

async function viewSession(id) {
  try {
    const data = await api(`/runtime/sessions/${id}`);
    $('#session-detail').innerHTML = `<pre class="json">${JSON.stringify(data, null, 2)}</pre>`;
    const debrief = await api(`/runtime/sessions/${id}/debrief`);
    $('#session-debrief').innerHTML = `
      <div class="panel">
        <h2>Debrief</h2>
        <p>${debrief.headline}</p>
        <ul>${debrief.observations.map(o => `<li>${o}</li>`).join('')}</ul>
        <p>Columns: ${debrief.top_columns.join(', ')}</p>
      </div>
    `;
  } catch (e) { alert(e.message); }
}

function initUpload() {
  const drop = $('#upload-drop');
  const input = $('#upload-input');
  if (!drop) return;

  drop.addEventListener('click', () => input.click());
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('dragover'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
  drop.addEventListener('drop', e => {
    e.preventDefault();
    drop.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  input.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });
}

async function handleFile(file) {
  if (!file.name.endsWith('.csv') && !file.name.endsWith('.txt')) {
    alert('Only CSV/TXT runtime logs are supported.');
    return;
  }
  setLoading('upload', true);
  try {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/runtime/logs/parse`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    alert(`Parsed ${data.summary.rows} rows. Session: ${data.summary.session_id}`);
    loadSessions();
  } finally { setLoading('upload', false); }
}

/* ---------- Ingest ---------- */
async function loadIngestSources() {
  setLoading('ingest', true);
  try {
    state.ingestSources = await api('/ingest/sources');
    renderIngest();
  } finally { setLoading('ingest', false); }
}

function renderIngest() {
  const rows = state.ingestSources.map(s => `
    <tr>
      <td>${s.vendor}</td>
      <td>${s.native_extensions.join(', ')}</td>
      <td><span class="status-indicator ${s.available ? 'status-ok' : 'status-warn'}"></span>${s.available ? 'Ready' : 'Unavailable'}</td>
      <td>${s.notes || '—'}</td>
    </tr>
  `).join('');
  $('#ingest-table tbody').innerHTML = rows || '<tr><td colspan="4">No ingest sources registered.</td></tr>';
}

async function submitIngest() {
  const inputPath = $('#ingest-input-path').value;
  const outputDir = $('#ingest-output-dir').value || '.mea_tmp/normalized';
  const vendorHint = $('#ingest-vendor').value;
  if (!inputPath) return alert('Input path is required');
  setLoading('ingest-run', true);
  try {
    const res = await api('/ingest/normalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_path: inputPath, output_dir: outputDir, vendor_hint: vendorHint || undefined }),
    });
    $('#ingest-result').innerHTML = `<pre class="json">${JSON.stringify(res, null, 2)}</pre>`;
  } catch (e) { alert(e.message); }
  finally { setLoading('ingest-run', false); }
}

/* ---------- Jobs ---------- */
async function loadJob() {
  const id = $('#job-id-input').value.trim();
  if (!id) return;
  setLoading('job', true);
  try {
    const data = await api(`/jobs/${id}`);
    state.jobs[id] = data;
    $('#job-result').innerHTML = `<pre class="json">${JSON.stringify(data, null, 2)}</pre>`;
  } catch (e) { alert(e.message); }
  finally { setLoading('job', false); }
}

async function submitFixCI() {
  const repo = $('#fixci-repo').value.trim();
  const branch = $('#fixci-branch').value.trim();
  const patch = $('#fixci-patch').value.trim();
  if (!repo || !branch || !patch) return alert('All fields required');
  setLoading('fixci', true);
  try {
    const res = await api('/repos/fix-ci', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo, branch, patch }),
    });
    $('#fixci-result').innerHTML = `<pre class="json">${JSON.stringify(res, null, 2)}</pre>`;
  } catch (e) { alert(e.message); }
  finally { setLoading('fixci', false); }
}

/* ---------- Runtime State ---------- */
async function loadRuntimeState() {
  const sessionId = $('#state-session-id').value.trim() || 'default';
  setLoading('state', true);
  try {
    const [snapshot, events] = await Promise.all([
      api(`/runtime-state/snapshot?session_id=${encodeURIComponent(sessionId)}`).catch(() => null),
      api(`/runtime-state/events?session_id=${encodeURIComponent(sessionId)}`).catch(() => null),
    ]);
    state.runtimeSnapshot = snapshot;
    state.runtimeEvents = events?.events || [];
    renderRuntimeState();
  } finally { setLoading('state', false); }
}

function renderRuntimeState() {
  const snap = state.runtimeSnapshot;
  if (!snap) {
    $('#state-detail').innerHTML = '<div class="panel">No snapshot available. POST an event first.</div>';
    return;
  }
  $('#state-detail').innerHTML = `
    <div class="grid-3">
      <div class="panel"><h2>Agents</h2><div>Count: ${snap.summary?.agent_count || 0}</div></div>
      <div class="panel"><h2>Tasks</h2>
        ${Object.entries(snap.summary?.task_counts || {}).map(([k,v]) => `<div>${k}: ${v}</div>`).join('')}
      </div>
      <div class="panel"><h2>Seq / Hash</h2><div>Seq: ${snap.last_seq}</div><code style="font-size:0.75rem">${snap.last_state_hash}</code></div>
    </div>
    <div class="panel">
      <h2>Events</h2>
      <table><thead><tr><th>Seq</th><th>Type</th><th>Key</th><th>Hash</th></tr></thead><tbody>
      ${state.runtimeEvents.map(e => `<tr><td>${e.seq}</td><td>${e.event_type}</td><td>${e.idempotency_key}</td><td>${e.state_hash}</td></tr>`).join('')}
      </tbody></table>
    </div>
  `;
}

async function postRuntimeEvent() {
  const sessionId = $('#state-session-id').value.trim() || 'default';
  const type = $('#state-event-type').value;
  const key = $('#state-idempotency-key').value.trim() || crypto.randomUUID();
  const payloadRaw = $('#state-payload').value.trim();
  let payload = {};
  try { if (payloadRaw) payload = JSON.parse(payloadRaw); } catch { return alert('Invalid JSON payload'); }

  setLoading('state-post', true);
  try {
    const res = await api('/runtime-state/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer dev-token' },
      body: JSON.stringify({ idempotency_key: key, session_id: sessionId, event_type: type, payload }),
    });
    alert(`Event accepted: seq=${res.applied_seq}`);
    loadRuntimeState();
  } catch (e) { alert(e.message); }
  finally { setLoading('state-post', false); }
}

/* ---------- Init ---------- */
function init() {
  $$('nav button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));
  initUpload();
  setTab('dashboard');
  loadHealth();
  setInterval(loadHealth, 10000);
}

document.addEventListener('DOMContentLoaded', init);
