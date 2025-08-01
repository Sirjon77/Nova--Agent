
import traceback

def safe_run(module_func):
    try:
        print(f"[Tester] Running {module_func.__name__}")
        result = module_func()
        print(f"[Tester] Success: {result}")
    except Exception as e:
        print(f"[Tester] Error in {module_func.__name__}: {e}")
        traceback.print_exc()
