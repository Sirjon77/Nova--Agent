import json
from pathlib import Path

def load_nova_directive():
    path = Path("nova_master_prompt_v2.json")
    if not path.exists():
        return "Nova directive file not found."

    with open(path, "r") as f:
        data = json.load(f)

    # Use the new unified memory manager
    try:
        from utils.memory_manager import MemoryManager
        memory_manager = MemoryManager()
        memory_manager.add_long_term(
            namespace="system_directives",
            key="nova_master_prompt",
            content=data.get("content", ""),
            metadata={"version": "v1.0", "source": "bootloader"}
        )
        return "Nova directive loaded successfully using unified memory manager."
    except ImportError:
        # Fallback to old memory system if new manager not available
        from memory import save_to_memory
        save_to_memory(
            namespace="system_directives",
            key="nova_master_prompt",
            content=data.get("content", ""),
            metadata={"version": "v1.0", "source": "bootloader"}
        )
        return "Nova directive loaded successfully using legacy memory system."