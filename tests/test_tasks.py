import sys
import types
import pytest

class DummyCelery:
    """Dummy Celery class to simulate Celery decorator behavior for tests."""
    def __init__(self, name):
        self.name = name
    def config_from_object(self, obj):
        # No-op for configuration
        return None
    def task(self, *args, **kwargs):
        # Return a decorator that leaves the function unwrapped
        def decorator(func):
            return func
        return decorator

@pytest.fixture
def tasks_no_celery(monkeypatch):
    """
    Import the tasks module simulating an environment where Celery is not installed.
    This forces tasks.py to use the fallback no-op implementations.
    """
    # Ensure a clean import of tasks
    sys.modules.pop('tasks', None)
    
    # Mock dependencies that tasks.py imports
    # Mock platform_manager
    platform_manager_mod = types.ModuleType("platform_manager")
    def dummy_manage_platforms(video_path, prompt, prompt_id=None):
        return f"POSTED: {video_path}"
    platform_manager_mod.manage_platforms = dummy_manage_platforms
    monkeypatch.setitem(sys.modules, "platform_manager", platform_manager_mod)
    
    # Mock marketing_digest
    marketing_digest_mod = types.ModuleType("marketing_digest")
    def dummy_push_weekly_digest():
        return "DIGEST_PUSHED"
    def dummy_generate_landing_pages(num_pages=3, output_dir='landing_pages'):
        return "LANDING_PAGES_GENERATED"
    marketing_digest_mod.push_weekly_digest_to_notion = dummy_push_weekly_digest
    marketing_digest_mod.generate_landing_pages_for_top_prompts = dummy_generate_landing_pages
    monkeypatch.setitem(sys.modules, "marketing_digest", marketing_digest_mod)
    
    # Insert a dummy 'celery' module without a Celery class to trigger import failure
    orig_celery_mod = sys.modules.get('celery')
    dummy_mod = types.ModuleType("celery")
    monkeypatch.setitem(sys.modules, 'celery', dummy_mod)
    
    # Import the tasks module (Celery import will fail, Celery=None path taken)
    import tasks
    yield tasks
    
    # Cleanup: remove tasks module and restore original celery module
    sys.modules.pop('tasks', None)
    if orig_celery_mod is not None:
        sys.modules['celery'] = orig_celery_mod
    else:
        sys.modules.pop('celery', None)

@pytest.fixture
def tasks_celery(monkeypatch):
    """
    Import the tasks module with a dummy Celery available.
    Simulates Celery being installed so that tasks.py registers actual tasks.
    """
    # Ensure a clean import of tasks
    sys.modules.pop('tasks', None)
    
    # Mock dependencies that tasks.py imports
    # Mock platform_manager
    platform_manager_mod = types.ModuleType("platform_manager")
    def dummy_manage_platforms(video_path, prompt, prompt_id=None):
        return f"POSTED: {video_path}"
    platform_manager_mod.manage_platforms = dummy_manage_platforms
    monkeypatch.setitem(sys.modules, "platform_manager", platform_manager_mod)
    
    # Mock marketing_digest
    marketing_digest_mod = types.ModuleType("marketing_digest")
    def dummy_push_weekly_digest():
        return "DIGEST_PUSHED"
    def dummy_generate_landing_pages(num_pages=3, output_dir='landing_pages'):
        return "LANDING_PAGES_GENERATED"
    marketing_digest_mod.push_weekly_digest_to_notion = dummy_push_weekly_digest
    marketing_digest_mod.generate_landing_pages_for_top_prompts = dummy_generate_landing_pages
    monkeypatch.setitem(sys.modules, "marketing_digest", marketing_digest_mod)
    
    # Backup any existing celery module
    orig_celery_mod = sys.modules.get('celery')
    # Insert dummy Celery module with Celery class
    dummy_celery_mod = types.ModuleType("celery")
    dummy_celery_mod.Celery = DummyCelery
    monkeypatch.setitem(sys.modules, 'celery', dummy_celery_mod)
    
    # Import the tasks module (Celery import will succeed and tasks will use Celery branch)
    import tasks
    yield tasks
    
    # Cleanup: remove tasks module and restore original celery module
    sys.modules.pop('tasks', None)
    if orig_celery_mod is not None:
        sys.modules['celery'] = orig_celery_mod
    else:
        sys.modules.pop('celery', None)

# ============================================================================
# NO-CELERY FALLBACK MODE TESTS
# ============================================================================

def test_post_video_no_celery(tasks_no_celery, monkeypatch):
    """post_video should call manage_platforms and return its result when Celery is unavailable."""
    tasks = tasks_no_celery
    # Monkeypatch manage_platforms to track calls and supply a return value
    called_args = {}
    def dummy_manage(video_path, prompt, prompt_id=None):
        called_args['args'] = (video_path, prompt, prompt_id)
        return "POSTED"
    monkeypatch.setattr(tasks, "manage_platforms", dummy_manage)
    # Call the function
    result = tasks.post_video("video.mp4", "Test Prompt", "pid123")
    # Validate that manage_platforms was called with correct arguments and result passed through
    assert result == "POSTED"
    assert called_args.get('args') == ("video.mp4", "Test Prompt", "pid123")

def test_weekly_digest_no_celery(tasks_no_celery, monkeypatch):
    """weekly_digest should call push_weekly_digest_to_notion and generate_landing_pages_for_top_prompts, then return the success message."""
    tasks = tasks_no_celery
    # Monkeypatch the digest and landing page functions
    flags = {'digest_called': False, 'landing_called': False}
    def dummy_push():
        flags['digest_called'] = True
    def dummy_generate(num_pages=3, output_dir='landing_pages'):
        flags['landing_called'] = True
    monkeypatch.setattr(tasks, "push_weekly_digest_to_notion", dummy_push)
    monkeypatch.setattr(tasks, "generate_landing_pages_for_top_prompts", dummy_generate)
    # Call the function
    result = tasks.weekly_digest()
    # Validate that both functions were called and the return value is correct
    assert result == "Weekly digest and landing pages generated"
    assert flags['digest_called'] is True and flags['landing_called'] is True

def test_competitor_analysis_no_celery(tasks_no_celery, monkeypatch):
    """competitor_analysis should return an empty list in fallback mode (Celery unavailable)."""
    tasks = tasks_no_celery
    # Even if environment variable is set or seeds are provided, fallback ignores them and returns []
    monkeypatch.setenv('COMPETITOR_SEEDS', 'seed1,seed2')
    result1 = tasks.competitor_analysis()             # no seeds provided
    result2 = tasks.competitor_analysis(['x'], count=5)  # seeds provided (should be ignored in fallback)
    assert result1 == [] and result2 == []

def test_process_metrics_no_celery(tasks_no_celery):
    """process_metrics should return empty retired and leaderboard lists in fallback mode."""
    tasks = tasks_no_celery
    result = tasks.process_metrics()
    assert result == {'retired': [], 'leaderboard': []}

def test_suggest_hashtags_no_celery_import_fail(tasks_no_celery):
    """suggest_hashtags should return [] if HashtagOptimizer import fails (fallback mode)."""
    tasks = tasks_no_celery
    # No monkeypatch for nova.hashtag_optimizer means import will fail -> expect []
    result = tasks.suggest_hashtags("topic1", count=5)
    assert result == []

def test_suggest_hashtags_no_celery_success(tasks_no_celery, monkeypatch):
    """suggest_hashtags (fallback) should return the list from HashtagOptimizer.suggest if the module is present."""
    tasks = tasks_no_celery
    # Dummy HashtagOptimizer that returns a predictable list (longer than count to test no truncation in fallback)
    class DummyOptimizer:
        def suggest(self, topic, count=10):
            return [f"{topic}_hash{i}" for i in range(count + 2)]
    # Inject dummy nova.hashtag_optimizer module
    nova_mod = types.ModuleType("nova")
    hash_mod = types.ModuleType("nova.hashtag_optimizer")
    setattr(hash_mod, "HashtagOptimizer", DummyOptimizer)
    nova_mod.hashtag_optimizer = hash_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.hashtag_optimizer", hash_mod)
    # Call suggest_hashtags - should use DummyOptimizer.suggest
    result = tasks.suggest_hashtags("testtopic", count=3)
    # Dummy suggest returns 5 items (3+2); fallback mode does NOT truncate the list
    assert isinstance(result, list)
    assert len(result) == 5  # no truncation in fallback mode
    assert all(item.startswith("testtopic_hash") for item in result)

def test_suggest_hashtags_no_celery_exception(tasks_no_celery, monkeypatch):
    """suggest_hashtags (fallback) should return [] if HashtagOptimizer.suggest raises an exception."""
    tasks = tasks_no_celery
    # Dummy HashtagOptimizer that raises an error on suggest
    class DummyOptimizer:
        def suggest(self, topic, count=10):
            raise RuntimeError("suggest failed")
    nova_mod = types.ModuleType("nova")
    hash_mod = types.ModuleType("nova.hashtag_optimizer")
    setattr(hash_mod, "HashtagOptimizer", DummyOptimizer)
    nova_mod.hashtag_optimizer = hash_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.hashtag_optimizer", hash_mod)
    # Call suggest_hashtags - the exception should be caught and [] returned
    result = tasks.suggest_hashtags("topicfail", count=2)
    assert result == []

# ============================================================================
# CELERY-ENABLED MODE TESTS - BASIC TASKS
# ============================================================================

def test_post_video_with_celery(tasks_celery, monkeypatch):
    """post_video (Celery mode) should call manage_platforms and return its result."""
    tasks = tasks_celery
    called = {}
    def dummy_manage(video_path, prompt, prompt_id=None):
        called['args'] = (video_path, prompt, prompt_id)
        return "DONE"
    monkeypatch.setattr(tasks, "manage_platforms", dummy_manage)
    result = tasks.post_video("file.mp4", "Prompt", None)
    assert result == "DONE"
    assert called.get('args') == ("file.mp4", "Prompt", None)

def test_weekly_digest_with_celery(tasks_celery, monkeypatch):
    """weekly_digest (Celery mode) should call the underlying functions and return the success message."""
    tasks = tasks_celery
    called = {'digest': False, 'landing': False}
    def dummy_push():
        called['digest'] = True
    def dummy_gen(num_pages=3, output_dir='landing_pages'):
        called['landing'] = True
    monkeypatch.setattr(tasks, "push_weekly_digest_to_notion", dummy_push)
    monkeypatch.setattr(tasks, "generate_landing_pages_for_top_prompts", dummy_gen)
    result = tasks.weekly_digest()
    assert result == "Weekly digest and landing pages generated"
    assert called['digest'] is True and called['landing'] is True

# ============================================================================
# CELERY-ENABLED MODE TESTS - COMPETITOR ANALYSIS
# ============================================================================

def test_competitor_analysis_with_celery_no_module(tasks_celery):
    """competitor_analysis (Celery mode) should return [] if CompetitorAnalyzer import fails."""
    tasks = tasks_celery
    # Ensure no competitor_analyzer module so import inside function fails
    sys.modules.pop('nova.competitor_analyzer', None)
    result = tasks.competitor_analysis(seeds=None, count=5)
    assert result == []

@pytest.mark.parametrize("seeds_param, env_val, expected_seeds", [
    (["direct1", "direct2"], "env_should_not_be_used", ["direct1", "direct2"]),
    (None, " foo, bar ,, key3 ", ["foo", "bar", "key3"]),
])
def test_competitor_analysis_with_celery_module(tasks_celery, monkeypatch, seeds_param, env_val, expected_seeds):
    """competitor_analysis (Celery mode) uses CompetitorAnalyzer when available, parsing seeds correctly."""
    tasks = tasks_celery
    # Dummy CompetitorAnalyzer class to capture inputs and simulate output
    captured = {}
    class DummyAnalyzer:
        def __init__(self, cfg):
            captured['cfg'] = cfg  # capture config if needed
        async def benchmark_competitors(self, seeds, count):
            captured['seeds'] = seeds
            captured['count'] = count
            return [{"result": "ok", "seeds": seeds, "count": count}]
    # Inject dummy nova.competitor_analyzer module
    nova_mod = types.ModuleType("nova")
    comp_mod = types.ModuleType("nova.competitor_analyzer")
    setattr(comp_mod, "CompetitorAnalyzer", DummyAnalyzer)
    nova_mod.competitor_analyzer = comp_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.competitor_analyzer", comp_mod)
    # Set environment variable for seeds if no seeds_param provided
    monkeypatch.setenv("COMPETITOR_SEEDS", env_val)
    # Call competitor_analysis with either a direct seeds list or None (to trigger env usage)
    result = tasks.competitor_analysis(seeds=seeds_param, count=3)
    # Verify that we got a list result and the dummy analyzer returned the expected structure
    assert isinstance(result, list) and result and result[0].get("result") == "ok"
    # Check that seeds were parsed/used correctly
    assert captured.get('seeds') == expected_seeds
    assert captured.get('count') == 3

# ============================================================================
# CELERY-ENABLED MODE TESTS - PROCESS METRICS
# ============================================================================

def test_process_metrics_with_celery_no_module(tasks_celery):
    """process_metrics (Celery mode) should return empty dict if platform_metrics import fails."""
    tasks = tasks_celery
    # Ensure no platform_metrics module so import fails
    sys.modules.pop('nova.platform_metrics', None)
    result = tasks.process_metrics()
    assert result == {'retired': [], 'leaderboard': []}

@pytest.mark.parametrize("env_value, expected_threshold", [
    ("2.5", 2.5),           # valid float string
    ("not_a_number", 1.0),  # invalid value should fall back to 1.0
])
def test_process_metrics_with_celery_module(tasks_celery, monkeypatch, env_value, expected_threshold):
    """process_metrics (Celery mode) should use retire_underperforming and get_platform_leaderboard with correct threshold."""
    tasks = tasks_celery
    # Dummy platform_metrics functions to capture threshold and return dummy data
    captured = {}
    def dummy_retire_underperforming(metric, threshold):
        captured['threshold'] = threshold
        return ["p1"]
    def dummy_get_platform_leaderboard(metric):
        return {"p1": 123}
    # Inject dummy nova.platform_metrics module
    nova_mod = types.ModuleType("nova")
    metrics_mod = types.ModuleType("nova.platform_metrics")
    setattr(metrics_mod, "retire_underperforming", dummy_retire_underperforming)
    setattr(metrics_mod, "get_platform_leaderboard", dummy_get_platform_leaderboard)
    nova_mod.platform_metrics = metrics_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.platform_metrics", metrics_mod)
    # Set the RETIRE_THRESHOLD environment variable
    monkeypatch.setenv("RETIRE_THRESHOLD", env_value)
    result = tasks.process_metrics()
    # It should return the combined results from our dummy functions
    assert result == {'retired': ["p1"], 'leaderboard': {"p1": 123}}
    # Verify that the threshold was parsed correctly
    assert captured.get('threshold') == expected_threshold

# ============================================================================
# CELERY-ENABLED MODE TESTS - SUGGEST HASHTAGS
# ============================================================================

def test_suggest_hashtags_with_celery_no_module(tasks_celery):
    """suggest_hashtags (Celery mode) should return [] if HashtagOptimizer import fails."""
    tasks = tasks_celery
    # Ensure no hashtag_optimizer module so import fails
    sys.modules.pop('nova.hashtag_optimizer', None)
    result = tasks.suggest_hashtags("topic", count=5)
    assert result == []

def test_suggest_hashtags_with_celery_dynamic(tasks_celery, monkeypatch):
    """suggest_hashtags (Celery mode) should use dynamic suggestion when HASHTAG_DYNAMIC is enabled."""
    tasks = tasks_celery
    # Dummy HashtagOptimizer that tracks calls and returns a list for dynamic/static
    global dummy_opt_instance
    dummy_opt_instance = None  # will hold the created optimizer instance
    class DummyOptimizer:
        def __init__(self):
            global dummy_opt_instance
            dummy_opt_instance = self
            self.dynamic_called = False
            self.static_called = False
        def suggest_dynamic(self, topic, count=10):
            self.dynamic_called = True
            # Return a list longer than 'count' to test truncation logic
            return [f"{topic}_dyn{i}" for i in range(count + 2)]
        def suggest(self, topic, count=10):
            self.static_called = True
            return [f"{topic}_static{i}" for i in range(count + 2)]
    # Inject dummy nova.hashtag_optimizer module
    nova_mod = types.ModuleType("nova")
    hash_mod = types.ModuleType("nova.hashtag_optimizer")
    setattr(hash_mod, "HashtagOptimizer", DummyOptimizer)
    nova_mod.hashtag_optimizer = hash_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.hashtag_optimizer", hash_mod)
    # Enable dynamic mode via environment
    monkeypatch.setenv("HASHTAG_DYNAMIC", "true")
    result = tasks.suggest_hashtags("MyTopic", count=3)
    # It should use suggest_dynamic and truncate the result to 3 items
    assert result == [f"MyTopic_dyn{i}" for i in range(3)]
    # Ensure the dummy optimizer was called appropriately
    assert dummy_opt_instance is not None
    assert dummy_opt_instance.dynamic_called is True and dummy_opt_instance.static_called is False

def test_suggest_hashtags_with_celery_dynamic_fallback(tasks_celery, monkeypatch):
    """suggest_hashtags (Celery mode) should fall back to static suggestion if suggest_dynamic raises an exception."""
    tasks = tasks_celery
    global dummy_opt_instance
    dummy_opt_instance = None
    class DummyOptimizer:
        def __init__(self):
            global dummy_opt_instance
            dummy_opt_instance = self
            self.dynamic_called = False
            self.static_called = False
        def suggest_dynamic(self, topic, count=10):
            self.dynamic_called = True
            raise RuntimeError("Dynamic failed")
        def suggest(self, topic, count=10):
            self.static_called = True
            return [f"{topic}_fallback{i}" for i in range(count + 1)]
    nova_mod = types.ModuleType("nova")
    hash_mod = types.ModuleType("nova.hashtag_optimizer")
    setattr(hash_mod, "HashtagOptimizer", DummyOptimizer)
    nova_mod.hashtag_optimizer = hash_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.hashtag_optimizer", hash_mod)
    monkeypatch.setenv("HASHTAG_DYNAMIC", "yes")
    result = tasks.suggest_hashtags("TopicX", count=2)
    # Dynamic call fails, so it should use suggest() and then truncate to 2
    assert result == ["TopicX_fallback0", "TopicX_fallback1"]
    assert dummy_opt_instance is not None
    assert dummy_opt_instance.dynamic_called is True and dummy_opt_instance.static_called is True

def test_suggest_hashtags_with_celery_static(tasks_celery, monkeypatch):
    """suggest_hashtags (Celery mode) should use static suggestion when HASHTAG_DYNAMIC is disabled or 'false'."""
    tasks = tasks_celery
    global dummy_opt_instance
    dummy_opt_instance = None
    class DummyOptimizer:
        def __init__(self):
            global dummy_opt_instance
            dummy_opt_instance = self
            self.dynamic_called = False
            self.static_called = False
        def suggest_dynamic(self, topic, count=10):
            self.dynamic_called = True
            return [f"{topic}_dyn_should_not_be_used"]
        def suggest(self, topic, count=10):
            self.static_called = True
            return [f"{topic}_stat{i}" for i in range(count + 3)]
    nova_mod = types.ModuleType("nova")
    hash_mod = types.ModuleType("nova.hashtag_optimizer")
    setattr(hash_mod, "HashtagOptimizer", DummyOptimizer)
    nova_mod.hashtag_optimizer = hash_mod
    monkeypatch.setitem(sys.modules, "nova", nova_mod)
    monkeypatch.setitem(sys.modules, "nova.hashtag_optimizer", hash_mod)
    # Disable dynamic mode
    monkeypatch.setenv("HASHTAG_DYNAMIC", "0")
    result = tasks.suggest_hashtags("TopicY", count=4)
    # Should use suggest() and truncate to 4
    assert result == [f"TopicY_stat{i}" for i in range(4)]
    assert dummy_opt_instance is not None
    assert dummy_opt_instance.dynamic_called is False and dummy_opt_instance.static_called is True 