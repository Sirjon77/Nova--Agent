"""
Nova Agent Self-Coding Module

This module provides autonomous code generation and modification capabilities.
Handles React UI modifications and module generation with proper error handling.
"""

import openai
import os
import json
import time
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
MEMORY_LOG = "nova_memory_log.json"
FRONTEND_DIR = "./frontend"

# Default model - use valid OpenAI model names
DEFAULT_MODEL = "gpt-4o-mini"  # Valid OpenAI model name

def log_memory_entry(prompt: str, response: str) -> None:
    """
    Log code generation activities to memory for future reference.
    
    Args:
        prompt: The original prompt/instruction
        response: The generated code or response
    """
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt,
        "response": response
    }
    
    try:
        if not os.path.exists(MEMORY_LOG):
            with open(MEMORY_LOG, "w") as f:
                json.dump([entry], f, indent=2)
        else:
            with open(MEMORY_LOG, "r+") as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=2)
        
        logger.info(f"Logged memory entry: {len(prompt)} chars prompt, {len(response)} chars response")
        
    except Exception as e:
        logger.error(f"Failed to log memory entry: {e}")

def write_module_from_instruction(task_description: str, filename: str = "new_module.py") -> Optional[str]:
    """
    Generate a Python module from a natural language description.
    
    Args:
        task_description: Natural language description of the module to create
        filename: Output filename for the generated module
        
    Returns:
        str: Generated filename if successful, None otherwise
    """
    reasoning = (
        "Analyze the task and break it into logical steps. "
        "Verify assumptions and use standard libraries unless a specific package is required."
    )

    full_prompt = f"{reasoning}\nTask: {task_description}"

    try:
        response = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,  # Fixed: use valid model name
            messages=[
                {"role": "system", "content": "You are Nova Agent's autonomous module builder."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3
        )

        code_output = response['choices'][0]['message']['content']

        with open(filename, "w") as f:
            f.write(code_output)

        log_memory_entry(full_prompt, code_output)
        logger.info(f"Generated module: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Failed to generate module: {e}")
        return None

def backup_frontend() -> bool:
    """
    Create a git backup of the frontend directory.
    
    Returns:
        bool: True if backup successful, False otherwise
    """
    try:
        if not os.path.isdir(".git"):
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "add", "."], cwd=FRONTEND_DIR, check=True)
            subprocess.run(["git", "commit", "-m", "Initial frontend snapshot"], cwd=FRONTEND_DIR, check=True)
            logger.info("Frontend backup created successfully")
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create frontend backup: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        return False

def modify_react_ui(instruction: str) -> str:
    """
    Modify React UI components based on natural language instructions.
    
    Args:
        instruction: Natural language instruction for UI modification
        
    Returns:
        str: Status message describing the modification result
    """
    target_file = os.path.join(FRONTEND_DIR, "NovaLiveInterface.jsx")
    
    if not os.path.exists(target_file):
        return "Error: Interface file not found."

    # Create backup before modifications
    backup_frontend()

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            original_code = f.read()

        # Fixed: Use f-string for proper string formatting
        if "add chart" in instruction.lower():
            patch = f"\n<div>📊 New chart placeholder inserted by Nova based on request: '{instruction}'</div>\n"
            updated_code = original_code.replace("</CardContent>", patch + "\n</CardContent>")
        else:
            return "Instruction understood but not yet supported."

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(updated_code)

        logger.info(f"Modified React UI: {target_file}")
        return f"Nova updated {target_file} based on instruction: {instruction}"
        
    except Exception as e:
        logger.error(f"Failed to modify React UI: {e}")
        return f"Error modifying UI: {e}"

class SelfCoder:
    """
    SelfCoder class for organizing code generation and modification operations.
    
    This class encapsulates the functionality for autonomous code generation,
    React UI modifications, and memory logging with proper error handling.
    """
    
    def __init__(self, frontend_dir: str = "./frontend", memory_log: str = "nova_memory_log.json"):
        self.frontend_dir = frontend_dir
        self.memory_log = memory_log
        self.logger = logging.getLogger(__name__)
    
    def generate_module(self, task_description: str, filename: str = "new_module.py") -> Optional[str]:
        """Generate a Python module from description."""
        return write_module_from_instruction(task_description, filename)
    
    def modify_ui(self, instruction: str) -> str:
        """Modify React UI based on instruction."""
        return modify_react_ui(instruction)
    
    def get_status(self) -> dict:
        """Get SelfCoder status and configuration."""
        return {
            "frontend_dir": self.frontend_dir,
            "memory_log": self.memory_log,
            "openai_available": bool(openai.api_key),
            "frontend_exists": os.path.exists(self.frontend_dir),
            "memory_log_exists": os.path.exists(self.memory_log)
        }
