import json
from pathlib import Path

def load_nova_directive():
    path = Path("nova_master_prompt_v2.json")
    if not path.exists():
        return "Nova directive file not found."

    with open(path, "r") as f:
        data = json.load(f)

    # Use the global memory manager
    try:
        from utils.memory_manager import get_global_memory_manager
        memory_manager = get_global_memory_manager()
        memory_manager.add_long_term(
            namespace="system_directives",
            key="nova_master_prompt",
            content=data.get("content", ""),
            metadata={"version": "v1.0", "source": "bootloader"}
        )
        return "Nova directive loaded successfully using global memory manager."
    except ImportError as e:
        return f"Failed to import memory manager: {e}"
    except Exception as e:
        return f"Failed to load Nova directive: {e}"