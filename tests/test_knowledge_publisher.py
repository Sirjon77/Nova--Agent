from utils.knowledge_publisher import publish_reflection

class TestKnowledgePublisher:
    def test_publish_reflection_with_client(self):
        """Test publishing reflection when weaviate client is available."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            publish_reflection("test_session", "Test reflection content", ["test", "reflection"])
            
            mock_client.data_object.create.assert_called_once()
            call_args = mock_client.data_object.create.call_args
            assert call_args[1]["class_name"] == "GlobalReflection"

    def test_publish_reflection_without_client(self):
        """Test publishing reflection when weaviate client is not available."""
        with patch('utils.knowledge_publisher.client', None):
            # Should not raise any exception
            publish_reflection("test_session", "Test reflection content")

    def test_publish_reflection_with_tags(self):
        """Test publishing reflection with tags."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            tags = ["important", "urgent"]
            publish_reflection("test_session", "Test content", tags)
            
            call_args = mock_client.data_object.create.call_args
            obj_data = call_args[0][0]  # First positional argument
            assert obj_data["tags"] == tags

    def test_publish_reflection_without_tags(self):
        """Test publishing reflection without tags."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            publish_reflection("test_session", "Test content")
            
            call_args = mock_client.data_object.create.call_args
            obj_data = call_args[0][0]  # First positional argument
            assert obj_data["tags"] == []

    def test_publish_reflection_session_id(self):
        """Test that session_id is correctly set."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            session_id = "unique_session_123"
            publish_reflection(session_id, "Test content")
            
            call_args = mock_client.data_object.create.call_args
            obj_data = call_args[0][0]  # First positional argument
            assert obj_data["session_id"] == session_id

    def test_publish_reflection_content(self):
        """Test that content is correctly set."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            content = "This is test reflection content"
            publish_reflection("test_session", content)
            
            call_args = mock_client.data_object.create.call_args
            obj_data = call_args[0][0]  # First positional argument
            assert obj_data["content"] == content

    def test_publish_reflection_timestamp(self):
        """Test that timestamp is set."""
        with patch('utils.knowledge_publisher.client') as mock_client:
            mock_client.data_object.create = Mock()
            
            publish_reflection("test_session", "Test content")
            
            call_args = mock_client.data_object.create.call_args
            obj_data = call_args[0][0]  # First positional argument
            assert "timestamp" in obj_data
            assert isinstance(obj_data["timestamp"], (int, float)) 