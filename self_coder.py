
import openai
import os
import json
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
MEMORY_LOG = "nova_memory_log.json"

def log_memory_entry(prompt, response):
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt,
        "response": response
    }
    if not os.path.exists(MEMORY_LOG):
        with open(MEMORY_LOG, "w") as f:
            json.dump([entry], f, indent=2)
    else:
        with open(MEMORY_LOG, "r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)

def write_module_from_instruction(task_description, filename="new_module.py"):
    reasoning = (
        "Analyze the task and break it into logical steps. "
        "Verify assumptions and use standard libraries unless a specific package is required."
    )

    full_prompt = f"{reasoning}\nTask: {task_description}"

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Nova Agent’s autonomous module builder."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.3
    )

    code_output = response['choices'][0]['message']['content']

    with open(filename, "w") as f:
        f.write(code_output)

    log_memory_entry(full_prompt, code_output)
    print(f"[Nova Self-Coder] Generated module: {filename}")
    return filename



import subprocess
import os

FRONTEND_DIR = "./frontend"

def backup_frontend():
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"])
        subprocess.run(["git", "add", "."], cwd=FRONTEND_DIR)
        subprocess.run(["git", "commit", "-m", "Initial frontend snapshot"], cwd=FRONTEND_DIR)

def modify_react_ui(instruction):
    from openai import OpenAI  # or use local logic if offline
    target_file = os.path.join(FRONTEND_DIR, "NovaLiveInterface.jsx")
    if not os.path.exists(target_file):
        return "Error: Interface file not found."

    backup_frontend()

    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    # Simulate diff-based instruction logic (replace with OpenAI call if live)
    if "add chart" in instruction.lower():
        patch = "\n<div>📊 New chart placeholder inserted by Nova based on request: '{instruction}'</div>\n"
        updated_code = original_code.replace("</CardContent>", patch + "\n</CardContent>")
    else:
        return "Instruction understood but not yet supported."

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_code)

    return f"Nova updated {target_file} based on instruction: {instruction}"
