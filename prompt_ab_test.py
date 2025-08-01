
import random
import json
from datetime import datetime

class PromptABTest:
    def __init__(self):
        self.variants = {}

    def create_test(self, prompt_id, versions):
        self.variants[prompt_id] = {
            'A': versions[0],
            'B': versions[1],
            'log': []
        }

    def run_test(self, prompt_id):
        choice = random.choice(['A', 'B'])
        variant = self.variants[prompt_id][choice]
        self.log_result(prompt_id, choice)
        return variant

    def log_result(self, prompt_id, variant_used):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'variant': variant_used
        }
        self.variants[prompt_id]['log'].append(entry)
        with open("ab_test_log.json", "w") as f:
            json.dump(self.variants, f, indent=2)
