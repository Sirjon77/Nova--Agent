from nova.policy import PolicyEnforcer
import yaml, tempfile, pathlib

def _tmp_policy(data):
    p = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
    yaml.safe_dump(data, p)
    p.close()
    return p.name

def test_tool_block():
    pol_file = _tmp_policy({'sandbox': {'allowed_tools': ['google_trends']}})
    pe = PolicyEnforcer(pol_file)
    assert pe.tool_allowed('google_trends') is True
    assert pe.tool_allowed('blocked_tool') is False

def test_memory_no_limit():
    pe = PolicyEnforcer(_tmp_policy({}))
    assert pe.check_memory() is True
