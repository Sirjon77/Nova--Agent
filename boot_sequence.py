
import json
from agent_spawner import AgentSpawner
from nova_supervisor import require_nova_approval

CONFIG_FILE = "crew_config.json"

@require_nova_approval
def run_boot_sequence():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load crew config: {e}")
        return

    spawner = AgentSpawner()
    for crew_name, agents in config.items():
        for agent in agents:
            print(f"🧠 Booting {agent['name']} in {crew_name}")
            spawner.spawn_agent(
                role_description=agent["role"],
                tools=[],
                goal=agent["goal"]
            )
