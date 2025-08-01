import json
from pathlib import Path
from memory import save_to_memory

def load_nova_directive():
    path = Path("nova_master_prompt_v2.json")
    if not path.exists():
        return "Nova directive file not found."

    with open(path, "r") as f:
        data = json.load(f)

    save_to_memory(
        namespace="system_directives",
        key="nova_master_prompt",
        content=data.get("content", ""),
        metadata={"version": "v1.0", "source": "bootloader"}
    )
    return "Nova directive loaded successfully."