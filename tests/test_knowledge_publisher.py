import pytest
import tempfile
import os
from utils.knowledge_publisher import KnowledgePublisher

class TestKnowledgePublisher:
    def test_initialization(self):
        """Test KnowledgePublisher class initialization."""
        publisher = KnowledgePublisher()
        assert publisher is not None

    def test_publish_knowledge_valid(self):
        """Test publishing valid knowledge."""
        publisher = KnowledgePublisher()
        knowledge = {
            "title": "Test Knowledge",
            "content": "This is test content",
            "tags": ["test", "knowledge"],
            "source": "test_source"
        }
        result = publisher.publish(knowledge)
        assert result.success is True
        assert result.knowledge_id is not None

    def test_publish_knowledge_invalid(self):
        """Test publishing invalid knowledge."""
        publisher = KnowledgePublisher()
        # Missing required fields
        knowledge = {"title": "Test"}
        result = publisher.publish(knowledge)
        assert result.success is False
        assert "content" in result.error_message

    def test_validate_knowledge_structure(self):
        """Test knowledge structure validation."""
        publisher = KnowledgePublisher()
        valid_knowledge = {
            "title": "Test",
            "content": "Content",
            "tags": ["tag1"],
            "source": "source1"
        }
        assert publisher.validate_structure(valid_knowledge) is True

    def test_validate_knowledge_structure_invalid(self):
        """Test knowledge structure validation with invalid data."""
        publisher = KnowledgePublisher()
        invalid_knowledge = {"title": "Test"}  # Missing required fields
        assert publisher.validate_structure(invalid_knowledge) is False

    def test_search_knowledge(self):
        """Test knowledge search functionality."""
        publisher = KnowledgePublisher()
        # First publish some knowledge
        knowledge = {
            "title": "Search Test",
            "content": "This is searchable content",
            "tags": ["search", "test"],
            "source": "test_source"
        }
        publisher.publish(knowledge)
        
        # Search for the knowledge
        results = publisher.search("searchable")
        assert len(results) > 0
        assert any("Search Test" in result.title for result in results)

    def test_get_knowledge_by_id(self):
        """Test retrieving knowledge by ID."""
        publisher = KnowledgePublisher()
        knowledge = {
            "title": "ID Test",
            "content": "Content for ID test",
            "tags": ["id", "test"],
            "source": "test_source"
        }
        result = publisher.publish(knowledge)
        knowledge_id = result.knowledge_id
        
        retrieved = publisher.get_by_id(knowledge_id)
        assert retrieved is not None
        assert retrieved.title == "ID Test"

    def test_update_knowledge(self):
        """Test updating existing knowledge."""
        publisher = KnowledgePublisher()
        knowledge = {
            "title": "Update Test",
            "content": "Original content",
            "tags": ["update", "test"],
            "source": "test_source"
        }
        result = publisher.publish(knowledge)
        knowledge_id = result.knowledge_id
        
        # Update the knowledge
        updated_knowledge = {
            "title": "Updated Test",
            "content": "Updated content",
            "tags": ["updated", "test"],
            "source": "test_source"
        }
        update_result = publisher.update(knowledge_id, updated_knowledge)
        assert update_result.success is True
        
        # Verify the update
        retrieved = publisher.get_by_id(knowledge_id)
        assert retrieved.title == "Updated Test"
        assert retrieved.content == "Updated content"

    def test_delete_knowledge(self):
        """Test deleting knowledge."""
        publisher = KnowledgePublisher()
        knowledge = {
            "title": "Delete Test",
            "content": "Content to delete",
            "tags": ["delete", "test"],
            "source": "test_source"
        }
        result = publisher.publish(knowledge)
        knowledge_id = result.knowledge_id
        
        # Delete the knowledge
        delete_result = publisher.delete(knowledge_id)
        assert delete_result.success is True
        
        # Verify deletion
        retrieved = publisher.get_by_id(knowledge_id)
        assert retrieved is None 