
# nova_supervisor.py
import functools

def require_nova_approval(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        approved = True  # Future: load approval logic from a config/memory reflection
        if not approved:
            raise PermissionError("Nova has not approved this action.")
        return func(*args, **kwargs)
    return wrapper

# --- Apex v4 meta-agents injection ---
try:
    from meta_reflection_engine import run_meta_reflection
    from diagnostic_repair_agent import run_diagnostic_repair
    from prompt_feedback_loop import adapt_prompts
    from agent_delegator import delegator_loop
    import threading
    import time

    def _bg(target, interval):
        def loop():
            while True:
                try:
                    target()
                except Exception as exc:
                    print('[Apex meta-agent] Error in', target.__name__, exc)
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()

    _bg(run_meta_reflection, 1800)  # 30 min
    _bg(run_diagnostic_repair, 300) # 5 min
    _bg(adapt_prompts, 900)         # 15 min
    _bg(delegator_loop, 60)         # 1 min
    print('[Apex] Meta-agents started')
except Exception as e:
    print('[Apex] Meta-agent injection failed:', e)
# --- End Apex patch ---
