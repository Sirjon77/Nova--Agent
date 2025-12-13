
import json
import datetime
import os

def run_loop_health_check(stage='boot'):
    report = {
        "stage": stage,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "PASS",
        "modules_checked": 5,
        "errors": [],
        "warnings": []
    }

    required_files = ["nova_loop.py", "memory.py", "caption_writer.py", "ab_test_log.json"]
    for file in required_files:
        if not os.path.exists(file):
            report["errors"].append(f"Missing: {file}")
            report["status"] = "FAIL"

    with open("loop_health_report.json", "w") as f_out:
        json.dump(report, f_out, indent=2)
