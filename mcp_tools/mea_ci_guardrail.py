from typing import Any, Dict

def run_mea_ci_guardrail(args: Dict[str, Any]) -> Dict[str, Any]:
    args["ci_state"]
    proposed_patch = args.get("proposed_patch")

    if not proposed_patch:
        return {
            "uncertain": True,
            "safe_action": "ask_clarifying_question",
            "normalized_patch": None,
            "reason": "No patch provided; cannot safely modify repository."
        }

    lines = proposed_patch.splitlines()
    if len(lines) > 500:
        return {
            "uncertain": True,
            "safe_action": "do_nothing",
            "normalized_patch": None,
            "reason": "Patch too large; likely to cause unintended changes."
        }

    touched_paths = [ln[4:].strip() for ln in lines if ln.startswith("+++ ")]
    signal_paths = (".github/workflows" in " ".join(touched_paths)) or ("tests/" in " ".join(touched_paths)) or ("src/" in " ".join(touched_paths))

    if not signal_paths:
        return {
            "uncertain": True,
            "safe_action": "do_nothing",
            "normalized_patch": None,
            "reason": "Patch does not appear related to failing CI/test paths."
        }

    return {
        "uncertain": False,
        "safe_action": "emit_patch",
        "normalized_patch": proposed_patch,
        "reason": "Patch is small and appears related to CI/test failures."
    }
