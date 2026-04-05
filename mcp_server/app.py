import os
from fastapi import FastAPI, Header, HTTPException

from mcp_tools.mea_ci_guardrail import run_mea_ci_guardrail
from mcp_tools.ralph_wiggum_agent import run_ralph_wiggum_agent
from shared.models import A2AInvokeRequest, A2AInvokeResponse, MCPProviderStatus, MCPToolCall
from shared.version import load_version_info

app = FastAPI(title="MEA MCP Server")

PROVIDER_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

TOOL_REGISTRY = {
    "mea_ci_guardrail": run_mea_ci_guardrail,
    "ralph_wiggum_agent": run_ralph_wiggum_agent,
}


def _check_shared_token(authorization: str | None):
    expected = os.environ.get("MCP_SHARED_BEARER_TOKEN", "")
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid_bearer_token")


@app.get("/healthz")
def healthz():
    version_info = load_version_info()
    return {
        "status": "ok",
        "kernel_version": version_info.kernel_version,
        "package_version": version_info.package_version,
    }


@app.get("/providers", response_model=list[MCPProviderStatus])
def providers():
    return [
        MCPProviderStatus(provider=name, env_var=env, configured=bool(os.environ.get(env)))
        for name, env in PROVIDER_ENV.items()
    ]


@app.post("/tools/call")
def call_tool(req: MCPToolCall, authorization: str | None = Header(default=None)):
    _check_shared_token(authorization)
    tool = TOOL_REGISTRY.get(req.name)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool_not_found")
    return tool(req.arguments)


@app.post("/a2a/invoke", response_model=A2AInvokeResponse)
def a2a_invoke(req: A2AInvokeRequest, authorization: str | None = Header(default=None)):
    _check_shared_token(authorization)
    required_env = PROVIDER_ENV[req.provider]
    configured = bool(os.environ.get(required_env))
    return A2AInvokeResponse(
        status="scaffolded",
        provider=req.provider,
        model=req.model,
        required_env=required_env,
        configured=configured,
        message="Provider bridge scaffold only. Inject the required API key and provider-specific transport to activate real calls.",
    )
