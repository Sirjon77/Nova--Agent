from .analyze_phase import analyze
from .plan_phase import plan
from .execute_phase import execute
from .respond_phase import respond

def run_phases(message: str, stream: bool = False):
    analysis = analyze(message)
    if stream:
        yield "analysis", analysis
    plan_obj = plan(analysis)
    if stream:
        yield "plan", plan_obj
    result = execute(plan_obj)
    if stream:
        yield "execute", result
    final = respond(result)
    if stream:
        yield "final", final
        return
    return final
