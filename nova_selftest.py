from utils.memory_manager import get_global_memory_manager

def run_nova_selftest():
    mm = get_global_memory_manager()
    directives = mm.get_relevant_memories("system_directives", namespace="system", top_k=5)
    if not directives:
        return "❌ No system directive found in memory."

    for d in directives:
        if "Nova" in d.get("content", ""):
            return "✅ Nova directive verified."
    return "❌ Nova directive mismatch or missing."