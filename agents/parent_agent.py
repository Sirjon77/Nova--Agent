"""Parent agent that delegates tasks to child helper agents."""
from agents.multi_step_planner import plan_and_execute

class ParentAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def handle_goal(self, goal: str, context: str = "") -> str:
        # create plan
        output = plan_and_execute(goal, context)
        return output
