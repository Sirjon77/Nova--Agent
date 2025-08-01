
import importlib
import os

MODULES = {}

def load_all_modules():
    module_dir = "modules"
    for filename in os.listdir(module_dir):
        if filename.endswith(".py"):
            mod_name = filename[:-3]
            mod_path = f"{module_dir}.{mod_name}"
            try:
                MODULES[mod_name] = importlib.import_module(mod_path)
                print(f"[ModuleLoader] Loaded: {mod_name}")
            except Exception as e:
                print(f"[ModuleLoader] Failed to load {mod_name}: {e}")

def get_module(name):
    return MODULES.get(name)
