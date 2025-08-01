from memory import query_memory

def run_nova_selftest():
    directives = query_memory("system_directives")
    if not directives:
        return "❌ No system directive found in memory."

    for d in directives:
        if "Nova" in d.get("content", ""):
            return "✅ Nova directive verified."
    return "❌ Nova directive mismatch or missing."