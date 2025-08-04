"""
Unified Memory Management System for Nova Agent

This module provides a single interface for all memory operations:
- Short-term memory (Redis)
- Long-term memory (Weaviate)
- File-based logging (JSON)
- Crawled summaries (JSON)

Consolidates all memory operations through a consistent interface.
"""

import json
import os
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Unified memory manager for Nova Agent.
    
    Handles all memory operations through a consistent interface:
    - Short-term: Redis for session data
    - Long-term: Weaviate for vector storage
    - File-based: JSON logs for persistence
    - Summaries: JSON storage for crawled content
    """
    
    def __init__(self, 
                 short_term_dir: str = "data/short_term",
                 long_term_dir: str = "data/long_term",
                 log_dir: str = "data/logs",
                 summaries_dir: str = "data/summaries"):
        """
        Initialize memory manager with storage directories.
        
        Args:
            short_term_dir: Directory for short-term memory files
            long_term_dir: Directory for long-term memory files
            log_dir: Directory for interaction logs
            summaries_dir: Directory for crawled summaries
        """
        self.short_term_dir = Path(short_term_dir)
        self.long_term_dir = Path(long_term_dir)
        self.log_dir = Path(log_dir)
        self.summaries_dir = Path(summaries_dir)
        
        # Create directories if they don't exist
        for directory in [self.short_term_dir, self.long_term_dir, self.log_dir, self.summaries_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory stores
        self._init_memory_stores()
        
        logger.info("MemoryManager initialized successfully")
    
    def _init_memory_stores(self):
        """Initialize different memory stores."""
        # Try to initialize Redis for short-term memory
        try:
            import redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis connected for short-term memory")
        except Exception as e:
            self.redis_available = False
            logger.warning(f"Redis not available for short-term memory: {e}")
        
        # Try to initialize Weaviate for long-term memory
        try:
            import weaviate
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            if weaviate_url and weaviate_api_key:
                # Test Weaviate connection
                client = weaviate.Client(
                    url=weaviate_url,
                    auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_api_key)
                )
                client.schema.get()  # Test connection
                self.weaviate_available = True
                logger.info("Weaviate connected for long-term memory")
            else:
                self.weaviate_available = False
                logger.warning("Weaviate not available - missing environment variables")
        except Exception as e:
            self.weaviate_available = False
            logger.warning(f"Failed to initialize Weaviate: {e}")
    
    def add_short_term(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add content to short-term memory (Redis or file fallback).
        
        Args:
            session_id: Session identifier
            role: Role (user, system, assistant)
            content: Content to store
            metadata: Optional metadata
            
        Returns:
            bool: True if stored successfully
        """
        try:
            if self.redis_available:
                # Store in Redis
                key = f"short_term:{session_id}:{int(time.time())}"
                data = {
                    "role": role,
                    "content": content,
                    "timestamp": time.time(),
                    "metadata": metadata or {}
                }
                self.redis_client.setex(key, 3600, json.dumps(data))  # 1 hour TTL
                logger.debug(f"Stored in Redis: {key}")
                return True
            else:
                # Fallback to file storage
                return self._store_short_term_file(session_id, role, content, metadata)
                
        except Exception as e:
            logger.error(f"Failed to add short-term memory: {e}")
            return False
    
    def add_long_term(self, namespace: str, key: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add content to long-term memory (Weaviate or file fallback).
        
        Args:
            namespace: Memory namespace
            key: Unique identifier
            content: Content to store
            metadata: Optional metadata
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Always use file storage for now - Weaviate integration handled separately
            return self._store_long_term_file(namespace, key, content, metadata)
                
        except Exception as e:
            logger.error(f"Failed to add long-term memory: {e}")
            return False
    
    def get_relevant_memories(self, query: str, namespace: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant memories based on query.
        
        Args:
            query: Search query
            namespace: Memory namespace to search
            top_k: Number of results to return
            
        Returns:
            List of relevant memory entries
        """
        try:
            # Always use file search for now - Weaviate integration handled separately
            return self._search_long_term_file(query, namespace, top_k)
                
        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return []
    
    def query_long_term(self, namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query long-term memory (alias for get_relevant_memories).
        
        Args:
            namespace: Memory namespace to search
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant memory entries
        """
        return self.get_relevant_memories(query, namespace, top_k)
    
    def get_short_term(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent short-term memories for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of entries to return
            
        Returns:
            List of recent memory entries
        """
        try:
            if self.redis_available:
                # Get from Redis
                pattern = f"short_term:{session_id}:*"
                keys = self.redis_client.keys(pattern)
                keys.sort(reverse=True)  # Most recent first
                
                memories = []
                for key in keys[:limit]:
                    data = self.redis_client.get(key)
                    if data:
                        memories.append(json.loads(data))
                
                return memories
            else:
                # Fallback to file storage
                return self._get_short_term_file(session_id, limit)
                
        except Exception as e:
            logger.error(f"Failed to get short-term memory: {e}")
            return []
    
    def add_summary(self, url: str, title: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a crawled summary to memory.
        
        Args:
            url: Source URL
            title: Page title
            summary: Generated summary
            metadata: Optional metadata
            
        Returns:
            bool: True if stored successfully
        """
        try:
            summary_file = self.summaries_dir / "summaries.json"
            
            summary_data = {
                "url": url,
                "title": title,
                "summary": summary,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            # Load existing summaries
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summaries = json.load(f)
            else:
                summaries = []
            
            # Add new summary
            summaries.append(summary_data)
            
            # Keep only last 1000 summaries to prevent file from growing too large
            if len(summaries) > 1000:
                summaries = summaries[-1000:]
            
            # Save back to file
            with open(summary_file, 'w') as f:
                json.dump(summaries, f, indent=2)
            
            logger.info(f"Added summary for: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add summary: {e}")
            return False
    
    def log_interaction(self, session_id: str, prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an interaction for debugging and analysis.
        
        Args:
            session_id: Session identifier
            prompt: User prompt
            response: Agent response
            metadata: Optional metadata
            
        Returns:
            bool: True if logged successfully
        """
        try:
            log_file = self.log_dir / f"interactions_{datetime.now().strftime('%Y%m')}.json"
            
            interaction_data = {
                "session_id": session_id,
                "timestamp": time.time(),
                "prompt": prompt,
                "response": response,
                "metadata": metadata or {}
            }
            
            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new interaction
            logs.append(interaction_data)
            
            # Keep only last 5000 interactions per month
            if len(logs) > 5000:
                logs = logs[-5000:]
            
            # Save back to file
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logger.debug(f"Logged interaction for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if memory system is fully available."""
        return self.redis_available or self.weaviate_available
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get status of all memory systems."""
        return {
            "redis_available": self.redis_available,
            "weaviate_available": self.weaviate_available,
            "fully_available": self.is_available(),
            "short_term_count": self._get_short_term_count(),
            "long_term_count": self._get_long_term_count(),
            "summary_count": self._get_summary_count(),
            "log_count": self._get_log_count()
        }
    
    def cleanup_old_memories(self, days: int = 30) -> int:
        """
        Clean up old memory entries.
        
        Args:
            days: Age threshold in days
            
        Returns:
            int: Number of entries cleaned up
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            cleaned_count = 0
            
            # Clean up Redis entries
            if self.redis_available:
                pattern = "short_term:*"
                keys = self.redis_client.keys(pattern)
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        entry = json.loads(data)
                        if entry.get("timestamp", 0) < cutoff_time:
                            self.redis_client.delete(key)
                            cleaned_count += 1
            
            # Clean up file-based memories
            cleaned_count += self._cleanup_old_files(cutoff_time)
            
            logger.info(f"Cleaned up {cleaned_count} old memory entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
            return 0
    
    # Private helper methods
    def _store_short_term_file(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Store short-term memory in file."""
        try:
            file_path = self.short_term_dir / f"{session_id}.json"
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    memories = json.load(f)
            else:
                memories = []
            
            memory_entry = {
                "role": role,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            memories.append(memory_entry)
            
            # Keep only last 100 entries per session
            if len(memories) > 100:
                memories = memories[-100:]
            
            with open(file_path, 'w') as f:
                json.dump(memories, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store short-term file: {e}")
            return False
    
    def _store_long_term_file(self, namespace: str, key: str, content: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Store long-term memory in file."""
        try:
            file_path = self.long_term_dir / f"{namespace}.json"
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    memories = json.load(f)
            else:
                memories = []
            
            memory_entry = {
                "key": key,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            memories.append(memory_entry)
            
            with open(file_path, 'w') as f:
                json.dump(memories, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store long-term file: {e}")
            return False
    
    def _search_long_term_file(self, query: str, namespace: str, top_k: int) -> List[Dict[str, Any]]:
        """Search long-term memory files."""
        try:
            file_path = self.long_term_dir / f"{namespace}.json"
            
            if not file_path.exists():
                return []
            
            with open(file_path, 'r') as f:
                memories = json.load(f)
            
            # Simple keyword search (could be enhanced with embeddings)
            results = []
            query_lower = query.lower()
            
            for memory in memories:
                content = memory.get("content", "").lower()
                if query_lower in content:
                    results.append(memory)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search long-term file: {e}")
            return []
    
    def _get_short_term_file(self, session_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get short-term memory from file."""
        try:
            file_path = self.short_term_dir / f"{session_id}.json"
            
            if not file_path.exists():
                return []
            
            with open(file_path, 'r') as f:
                memories = json.load(f)
            
            # Return most recent entries
            return memories[-limit:]
            
        except Exception as e:
            logger.error(f"Failed to get short-term file: {e}")
            return []
    
    def _get_short_term_count(self) -> int:
        """Get count of short-term memory entries."""
        try:
            if self.redis_available:
                return len(self.redis_client.keys("short_term:*"))
            else:
                total = 0
                for file_path in self.short_term_dir.glob("*.json"):
                    with open(file_path, 'r') as f:
                        memories = json.load(f)
                        total += len(memories)
                return total
        except Exception:
            return 0
    
    def _get_long_term_count(self) -> int:
        """Get count of long-term memory entries."""
        try:
            if self.weaviate_available:
                # This would require Weaviate query - simplified for now
                return 0
            else:
                total = 0
                for file_path in self.long_term_dir.glob("*.json"):
                    with open(file_path, 'r') as f:
                        memories = json.load(f)
                        total += len(memories)
                return total
        except Exception:
            return 0
    
    def _get_summary_count(self) -> int:
        """Get count of summary entries."""
        try:
            summary_file = self.summaries_dir / "summaries.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summaries = json.load(f)
                return len(summaries)
            return 0
        except Exception:
            return 0
    
    def _get_log_count(self) -> int:
        """Get count of log entries."""
        try:
            total = 0
            for file_path in self.log_dir.glob("interactions_*.json"):
                with open(file_path, 'r') as f:
                    logs = json.load(f)
                    total += len(logs)
            return total
        except Exception:
            return 0
    
    def _cleanup_old_files(self, cutoff_time: float) -> int:
        """Clean up old file-based memories."""
        cleaned_count = 0
        
        # Clean up old short-term files
        for file_path in self.short_term_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    memories = json.load(f)
                
                # Remove old entries
                original_count = len(memories)
                memories = [m for m in memories if m.get("timestamp", 0) >= cutoff_time]
                
                if len(memories) < original_count:
                    cleaned_count += (original_count - len(memories))
                    
                    if memories:
                        with open(file_path, 'w') as f:
                            json.dump(memories, f, indent=2)
                    else:
                        file_path.unlink()  # Delete empty file
                        
            except Exception as e:
                logger.error(f"Failed to cleanup file {file_path}: {e}")
        
        return cleaned_count

# Global memory manager instance
memory_manager = MemoryManager()

# Convenience functions for backward compatibility
def store_short(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Store content in short-term memory."""
    return memory_manager.add_short_term(session_id, role, content, metadata)

def store_long(session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Store content in long-term memory."""
    return memory_manager.add_long_term("general", f"{session_id}_{int(time.time())}", content, metadata)

def get_short(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get short-term memory for session."""
    return memory_manager.get_short_term(session_id, limit) 

def get_relevant_memories(query: str, namespace: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
    """Get relevant memories based on query."""
    return memory_manager.get_relevant_memories(query, namespace, top_k)

# Singleton MemoryManager for global access
_memory_manager: Optional["MemoryManager"] = None

def get_global_memory_manager() -> "MemoryManager":
    """
    Return a singleton MemoryManager so every module shares one connection pool.
    
    Returns:
        MemoryManager: Global singleton instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
        logger.info("Global MemoryManager singleton initialized")
    return _memory_manager

def is_available() -> bool:
    """
    Check if the global memory manager is available.
    
    Returns:
        bool: True if memory system is available
    """
    try:
        mm = get_global_memory_manager()
        return mm.is_available()
    except Exception:
        return False

def get_status() -> Dict[str, Any]:
    """
    Get status of the global memory manager.
    
    Returns:
        Dict[str, Any]: Memory system status
    """
    try:
        mm = get_global_memory_manager()
        return mm.get_memory_status()
    except Exception as e:
        return {
            "fully_available": False,
            "error": str(e),
            "weaviate_available": False,
            "redis_available": False
        } 