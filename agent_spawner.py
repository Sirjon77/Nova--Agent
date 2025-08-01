
# agent_spawner.py
import json
import uuid
import datetime
from crewai import Crew, Agent
from nova_supervisor import require_nova_approval

REGISTRY_PATH = "sub_agent_registry.json"

class AgentSpawner:
    def __init__(self):
        self.registry_file = REGISTRY_PATH

    @require_nova_approval
    def spawn_agent(self, role_description, tools=[], goal="Execute assigned task"):
        agent_id = str(uuid.uuid4())
        agent_name = f"{role_description.replace(' ', '')}Agent"
        created_at = datetime.datetime.utcnow().isoformat()

        agent = Agent(name=agent_name, role=role_description, goal=goal, tools=tools)
        crew = Crew(agents=[agent], tasks=[goal])

        entry = {
            "agent_name": agent_name,
            "status": "active",
            "created_at": created_at,
            "task": goal,
            "last_heartbeat": created_at
        }
        self._register_agent(entry)
        return crew

    def _register_agent(self, entry):
        try:
            with open(self.registry_file, 'r') as f:
                registry = json.load(f)
        except FileNotFoundError:
            registry = []

        registry.append(entry)
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
