from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
def test_frontend_shell_and_modules_exist():
    required=["index.html","design.css","app.js","lib/api.js","lib/router.js","lib/charts.js","lib/keyboard.js","lib/state.js","lib/polling.js","lib/events.js","lib/utils.js","pages/mission-control.js","pages/aero-studio.js","pages/race-engineering.js","pages/operations.js","pages/not-found.js"]
    assert all((FRONTEND/x).is_file() for x in required)
def test_shell_uses_static_app_and_four_routes():
    html=(FRONTEND/"index.html").read_text()
    assert 'href="/static/design.css"' in html and 'src="/static/app.js"' in html
    for route in ("mission-control","aero-studio","race-engineering","operations"): assert f'data-route="{route}"' in html
def test_api_client_enforces_request_id_and_deduplicates_polls():
    js=(FRONTEND/"lib/api.js").read_text();assert "x-request-id" in js and "inflight" in js and "AbortController" in js
def test_no_external_chart_dependency():
    js=(FRONTEND/"lib/charts.js").read_text();assert "getContext" in js and "chart.js" not in js.lower()
def test_page_modules_are_lazy_loaded_by_router():
    js=(FRONTEND/"lib/router.js").read_text();assert "import(" in js and "mission-control" in js and "operations" in js
def test_runtime_state_endpoints_are_mounted_by_included_session_router():
    backend=(ROOT/"control_plane/routes/session.py").read_text();assert '@router.get("/runtime-state/snapshot"' in backend and '@router.get("/runtime-state/events"' in backend and '@router.post("/runtime-state/events"' in backend
def test_frontend_endpoint_references_match_contract():
    refs=set()
    for path in (FRONTEND/"pages").glob("*.js"): refs.update(re.findall(r'["`](/(?:healthz(?:/dependencies)?|metrics|runtime/sessions|ingest/sources|aero/runs|runtime/logs/parse|runtime-state/snapshot)[^"`?]*)',path.read_text()))
    assert {"/healthz","/healthz/dependencies","/runtime/sessions","/ingest/sources","/aero/runs","/runtime/logs/parse","/runtime-state/snapshot"} <= refs
