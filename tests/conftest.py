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

# Import after mocking setup
from nova.api.app import app


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
        
        # Mock chat completions
        mock_chat_completion = Mock()
        mock_chat_completion.choices = [Mock()]
        mock_chat_completion.choices[0].message.content = "Mocked response"
        mock_chat_completion.choices[0].message.role = "assistant"
        mock_client.chat.completions.create.return_value = mock_chat_completion
        
        # Mock completions
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].text = "Mocked completion"
        mock_client.completions.create.return_value = mock_completion
        
        mock_openai_class.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def mock_weaviate():
    """Mock Weaviate client for all tests."""
    with patch('weaviate.Client') as mock_weaviate_class:
        mock_client = Mock()
        mock_client.is_ready.return_value = True
        mock_client.schema.get.return_value = {}
        mock_client.data_object.create.return_value = {"id": "test-id"}
        mock_client.data_object.get.return_value = {"id": "test-id", "properties": {}}
        mock_client.data_object.delete.return_value = True
        mock_client.query.get.return_value = Mock()
        mock_weaviate_class.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="session")
def mock_requests():
    """Mock requests library for HTTP calls."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.raise_for_status.return_value = None
        
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
    """Provide a temporary directory for test files."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_files(temp_dir) -> Generator[Dict[str, Path], None, None]:
    """Provide test file paths in temporary directory."""
    files = {
        'automation_flags': temp_dir / "automation_flags.json",
        'approvals': temp_dir / "approvals.json",
        'policy': temp_dir / "policy.yaml",
        'memory_short': temp_dir / "memory_short.json",
        'memory_long': temp_dir / "memory_long.json",
        'logs': temp_dir / "logs.json",
        'summaries': temp_dir / "summaries.json",
    }
    
    # Create files with default content
    files['automation_flags'].write_text('{"require_approval": false}')
    files['approvals'].write_text('[]')
    files['policy'].write_text('rules: []')
    files['memory_short'].write_text('[]')
    files['memory_long'].write_text('[]')
    files['logs'].write_text('[]')
    files['summaries'].write_text('[]')
    
    yield files


@pytest.fixture(scope="function")
def authenticated_client(test_env_vars) -> Generator[TestClient, None, None]:
    """Provide an authenticated TestClient."""
    # Set environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    client = TestClient(app)
    
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
    
    yield client
    
    # Cleanup
    for key in test_env_vars:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="function")
def unauthenticated_client() -> TestClient:
    """Provide an unauthenticated TestClient."""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_memory_manager():
    """Mock MemoryManager for testing."""
    with patch('utils.memory_manager.MemoryManager') as mock_class:
        mock_instance = Mock()
        
        # Mock status methods
        mock_instance.is_available.return_value = True
        mock_instance.get_status.return_value = {
            "redis_available": True,
            "weaviate_available": True,
            "file_available": True
        }
        
        # Mock storage methods
        mock_instance.store_short.return_value = True
        mock_instance.store_long.return_value = True
        mock_instance.get_short.return_value = {"test": "data"}
        mock_instance.get_long.return_value = {"test": "data"}
        mock_instance.delete_short.return_value = True
        mock_instance.delete_long.return_value = True
        
        # Mock singleton pattern
        mock_class.return_value = mock_instance
        mock_class._instance = mock_instance
        
        yield mock_instance


@pytest.fixture(scope="function")
def mock_security_validator():
    """Mock SecurityValidator to bypass validation in tests."""
    with patch('security_validator.SecurityValidator') as mock_class:
        mock_instance = Mock()
        mock_instance.validate_env_var.return_value = True
        mock_instance.validate_all.return_value = True
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_secret_manager():
    """Mock SecretManager for testing."""
    with patch('secret_manager.SecretManager') as mock_class:
        mock_instance = Mock()
        mock_instance.get_secret.return_value = "test-secret"
        mock_instance.audit_access.return_value = None
        mock_instance.check_rotation_needs.return_value = False
        mock_instance.get_health_report.return_value = {"status": "healthy"}
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_jwt_middleware():
    """Mock JWT middleware to bypass authentication in tests."""
    with patch('auth.jwt_middleware.get_jwt_secret') as mock_get_secret, \
         patch('auth.jwt_middleware.issue_token') as mock_issue_token:
        
        mock_get_secret.return_value = "test-secret-key-32-chars-long-for-testing-only"
        mock_issue_token.return_value = "test.jwt.token"
        
        yield {
            'get_secret': mock_get_secret,
            'issue_token': mock_issue_token
        }


@pytest.fixture(scope="function")
def mock_external_apis():
    """Mock all external API integrations."""
    mocks = {}
    
    # Mock various integration modules
    integration_modules = [
        'integrations.metricool',
        'integrations.publer', 
        'integrations.notion',
        'integrations.convertkit',
        'integrations.gumroad',
        'integrations.teams',
        'integrations.runway',
        'integrations.tubebuddy',
        'integrations.socialpilot',
        'integrations.beacons',
        'integrations.hubspot',
        'integrations.vidiq',
        'integrations.youtube',
        'integrations.instagram',
        'integrations.facebook',
        'integrations.tiktok',
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
