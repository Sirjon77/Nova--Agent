import yaml, builtins, importlib
from logging_conf import audit_logger

POLICY = yaml.safe_load(open('config/policy.yaml'))

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in POLICY.get('blocked_modules', []):
        audit_logger.warning('blocked_import', extra={'user': 'agent', 'module': name})
        raise ImportError(f'Module {name} blocked by policy')
    return importlib.__import__(name, globals, locals, fromlist, level)

builtins.__import__ = safe_import
