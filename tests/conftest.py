"""
Comprehensive test configuration and shared fixtures for Nova Agent.

This module provides centralized test infrastructure including:
- Redis mocking and connection handling
- OpenAI API mocking and client initialization
- JWT authentication bypass for testing
- Environment variable management
- Temporary file and directory management
- Database mocking and cleanup
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict
from unittest.mock import Mock, patch

import pytest
from starlette.testclient import TestClient

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock Redis at module level to prevent connection errors during import
with patch('redis.Redis') as mock_redis_class:
    mock_redis_instance = Mock()
    mock_redis_instance.set.return_value = True
    mock_redis_instance.get.return_value = None
    mock_redis_instance.delete.return_value = 1
    mock_redis_instance.exists.return_value = 0
    mock_redis_instance.ping.return_value = True
    mock_redis_instance.keys.return_value = []
    mock_redis_instance.hset.return_value = 1
    mock_redis_instance.hget.return_value = None
    mock_redis_instance.hgetall.return_value = {}
    mock_redis_instance.expire.return_value = True
    mock_redis_instance.ttl.return_value = -1

    # Mock connection pool
    mock_pool = Mock()
    mock_pool.get_connection.return_value = Mock()
    mock_redis_instance.connection_pool = mock_pool

    mock_redis_class.return_value = mock_redis_instance

# Import after mocking setup - this is necessary to prevent import errors
from nova.api.app import app  # noqa: E402


@pytest.fixture(scope="session")
def test_env_vars() -> Dict[str, str]:
    """Provide test environment variables."""
    return {
        # JWT Authentication (bypass security validation for tests)
        "JWT_SECRET_KEY": "test-secret-key-32-chars-long-for-testing-only",
        "NOVA_ADMIN_USERNAME": "admin",
        "NOVA_ADMIN_PASSWORD": "admin",

        # OpenAI API (mocked)
        "OPENAI_API_KEY": "sk-test-key-for-testing-only",

        # Redis (mocked)
        "REDIS_URL": "redis://localhost:6379/0",

        # Weaviate (mocked)
        "WEAVIATE_API_KEY": "test-weaviate-key",
        "WEAVIATE_URL": "http://localhost:8080",

        # Email (mocked)
        "EMAIL_PASSWORD": "test-email-password-16-chars",
        "EMAIL_USERNAME": "test@example.com",

        # Integration APIs (mocked)
        "METRICOOL_API_TOKEN": "test-metricool-token",
        "METRICOOL_ACCOUNT_ID": "test-account-id",
        "PUBLER_API_KEY": "test-publer-key",
        "PUBLER_WORKSPACE_ID": "test-workspace-id",
        "NOTION_API_KEY": "test-notion-key",
        "CONVERTKIT_API_KEY": "test-convertkit-key",
        "GUMROAD_API_KEY": "test-gumroad-key",

        # File paths
        "AUTOMATION_FLAGS_FILE": "test_automation_flags.json",
        "APPROVALS_FILE": "test_approvals.json",
        "POLICY_FILE": "config/policy.yaml",
    }


@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    """Mock Redis client for all tests."""
    with patch('redis.Redis') as mock_redis_class:
        # Create a mock Redis instance
        mock_redis_instance = Mock()

        # Mock common Redis operations
        mock_redis_instance.set.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.delete.return_value = 1
        mock_redis_instance.exists.return_value = 0
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.keys.return_value = []
        mock_redis_instance.hset.return_value = 1
        mock_redis_instance.hget.return_value = None
        mock_redis_instance.hgetall.return_value = {}
        mock_redis_instance.expire.return_value = True
        mock_redis_instance.ttl.return_value = -1

        # Mock connection pool
        mock_pool = Mock()
        mock_pool.get_connection.return_value = Mock()
        mock_redis_instance.connection_pool = mock_pool

        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture(scope="session")
def mock_openai():
    """Mock OpenAI client for all tests."""
    with patch('openai.OpenAI') as mock_openai_class:
        # Create a mock OpenAI client
        mock_client = Mock()

        # Mock chat completion
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock()]
        mock_chat_completion.choices[0].message.content = "Mocked response"
        mock_client.chat.completions.create.return_value = mock_chat_completion

        # Mock completion
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].text = "Mocked completion"
        mock_client.completions.create.return_value = mock_completion

        mock_openai_class.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def mock_weaviate():
    """Mock Weaviate client for all tests."""
    with patch('weaviate.WeaviateClient') as mock_weaviate_class:
        # Create a mock Weaviate client
        mock_client = Mock()
        mock_client.schema.get.return_value = {}
        mock_weaviate_class.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def mock_requests():
    """Mock requests library for all tests."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:

        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = "Mocked response"

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response
        mock_delete.return_value = mock_response

        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put,
            'delete': mock_delete
        }


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    yield temp_path
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def test_files(temp_dir) -> Generator[Dict[str, Path], None, None]:
    """Create test files in temporary directory."""
    files = {}

    # Create test JSON files
    files['automation_flags'] = temp_dir / "test_automation_flags.json"
    files['automation_flags'].write_text('{"feature_enabled": true}')

    files['approvals'] = temp_dir / "test_approvals.json"
    files['approvals'].write_text('{"pending": []}')

    files['policy'] = temp_dir / "test_policy.yaml"
    files['policy'].write_text('rules:\n  - name: test_rule\n    enabled: true')

    yield files


@pytest.fixture(scope="function")
def authenticated_client(test_env_vars) -> Generator[TestClient, None, None]:
    """Create an authenticated test client."""
    # Set environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value

    # Create test client
    client = TestClient(app)

    # Add authentication headers
    client.headers = {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }

    yield client

    # Clean up environment variables
    for key in test_env_vars:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def unauthenticated_client() -> TestClient:
    """Create an unauthenticated test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_memory_manager():
    """Mock memory manager for testing."""
    with patch('utils.memory_manager.MemoryManager') as mock_mm_class:
        mock_mm = Mock()
        mock_mm.add_short_term.return_value = True
        mock_mm.add_long_term.return_value = True
        mock_mm.get_short_term.return_value = [{"role": "user", "content": "test"}]
        mock_mm.get_relevant_memories.return_value = [{"content": "test memory"}]
        mock_mm.is_available.return_value = True
        mock_mm.get_memory_status.return_value = {
            "redis_available": True,
            "weaviate_available": True,
            "fully_available": True,
            "short_term_count": 1,
            "long_term_count": 1,
            "total_count": 2
        }
        mock_mm_class.return_value = mock_mm
        yield mock_mm


@pytest.fixture(scope="function")
def mock_security_validator():
    """Mock security validator for testing."""
    with patch('security_validator.validate_jwt_secret') as mock_validate:
        mock_validate.return_value = True
        yield mock_validate


@pytest.fixture(scope="function")
def mock_secret_manager():
    """Mock secret manager for testing."""
    with patch('secret_manager.get_secret') as mock_get_secret:
        mock_get_secret.return_value = "test-secret-value"
        yield mock_get_secret


@pytest.fixture(scope="function")
def mock_jwt_middleware():
    """Mock JWT middleware for testing."""
    with patch('auth.jwt_middleware.verify_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": "test-user",
            "role": "admin",
            "exp": 9999999999
        }
        yield mock_verify


@pytest.fixture(scope="function")
def mock_external_apis():
    """Mock external API integrations for testing."""
    mocks = {}

    # Mock integration modules
    integration_modules = [
        'integrations.facebook',
        'integrations.instagram',
        'integrations.youtube',
        'integrations.tiktok',
        'integrations.twitter',
        'integrations.linkedin',
        'integrations.convertkit',
        'integrations.gumroad',
        'integrations.notion',
        'integrations.slack',
        'integrations.hubspot',
        'integrations.metricool',
        'integrations.publer',
        'integrations.socialpilot',
        'integrations.tubebuddy',
        'integrations.vidiq',
        'integrations.translate',
        'integrations.tts',
        'integrations.murf',
        'integrations.naturalreader',
    ]

    for module in integration_modules:
        with patch(module) as mock_module:
            mocks[module] = mock_module

    yield mocks


@pytest.fixture(scope="function")
def mock_nova_modules():
    """Mock Nova core modules for testing."""
    mocks = {}

    nova_modules = [
        'nova.autonomous_research',
        'nova.governance.governance_loop',
        'nova.governance_scheduler',
        'nova.research_dashboard',
        'nova.observability',
        'nova.nlp.intent_classifier',
        'nova.nlp.context_manager',
        'nova.nlp.training_data',
        'nova.phases.pipeline',
        'nova.phases.analyze_phase',
        'nova.phases.plan_phase',
        'nova.phases.execute_phase',
        'nova.phases.respond_phase',
    ]

    for module in nova_modules:
        with patch(module) as mock_module:
            mocks[module] = mock_module

    yield mocks


@pytest.fixture(scope="function")
def mock_utils_modules():
    """Mock utility modules for testing."""
    mocks = {}

    utils_modules = [
        'utils.memory_manager',
        'utils.memory_vault',
        'utils.memory_ranker',
        'utils.memory_router',
        'utils.model_controller',
        'utils.model_router',
        'utils.openai_wrapper',
        'utils.prompt_store',
        'utils.retry',
        'utils.self_repair',
        'utils.summarizer',
        'utils.telemetry',
        'utils.tool_registry',
        'utils.tool_wrapper',
        'utils.user_feedback',
        'utils.code_validator',
        'utils.confidence',
        'utils.json_logger',
        'utils.logger',
        'utils.knowledge_publisher',
    ]

    for module in utils_modules:
        with patch(module) as mock_module:
            mocks[module] = mock_module

    yield mocks


# Global test configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if any(slow_keyword in item.nodeid.lower() for slow_keyword in
               ["slow", "heavy", "comprehensive", "full"]):
            item.add_marker(pytest.mark.slow)

        # Mark external service tests
        if any(external_keyword in item.nodeid.lower() for external_keyword in
               ["api", "http", "external", "service"]):
            item.add_marker(pytest.mark.external)
