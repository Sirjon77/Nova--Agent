
from memory_reflector import refine_code_snippets
from nova_selftest import run_nova_selftest

def run_reflection_loop():
    print("[Reflection Loop] Running diagnostics and self-improvement...")
    run_nova_selftest()
    refine_code_snippets()
