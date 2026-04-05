from __future__ import annotations

from pathlib import Path

from shared.models import AgentDecisionRequest, AgentDecisionResponse

_PROVIDER_ENV = {
    'openai': 'OPENAI_API_KEY',
    'anthropic': 'ANTHROPIC_API_KEY',
    'google': 'GOOGLE_API_KEY',
    'openrouter': 'OPENROUTER_API_KEY',
}


def queue_agent_decision(req: AgentDecisionRequest) -> AgentDecisionResponse:
    env_var = _PROVIDER_ENV[req.provider]
    supervisor_prompt_ref = str(Path('prompts') / 'supervisor_system_prompt.txt')
    return AgentDecisionResponse(
        status='accepted',
        session_id=req.session_id,
        run_id=req.run_id,
        trace_id=req.trace_id,
        queued_job='supervisor_decision',
        required_env=env_var,
        supervisor_prompt_ref=supervisor_prompt_ref,
    )
