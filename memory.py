"""
Memory Management System for Nova Agent

This module provides vector-based memory storage using Weaviate and sentence transformers.
Handles graceful degradation when dependencies are not available.
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    weaviate = None
    WEAVIATE_AVAILABLE = False
    logger.warning("Weaviate not available - memory features will be limited")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("Sentence transformers not available - vector embeddings disabled")

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients only if dependencies are available
client = None
embedder = None

if WEAVIATE_AVAILABLE and WEAVIATE_URL and WEAVIATE_API_KEY:
    try:
        client = weaviate.Client(
            url=WEAVIATE_URL,
            auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY),
            additional_headers={"X-OpenAI-Api-Key": OPENAI_API_KEY} if OPENAI_API_KEY else {}
        )
        logger.info("Weaviate client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Weaviate client: {e}")
        client = None

if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence transformer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize sentence transformer: {e}")
        embedder = None

def save_to_memory(namespace: str, key: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save content to vector memory with embeddings.
    
    Args:
        namespace: Memory namespace/class name
        key: Unique identifier for the content
        content: Text content to store
        metadata: Optional metadata dictionary
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    if not client or not embedder:
        logger.warning("Memory storage not available - missing Weaviate or sentence transformers")
        return False
    
    try:
        # Generate vector embedding
        vector = embedder.encode(content)
        
        # Prepare data object
        data_obj = {
            "key": key,
            "content": content,
            "metadata": metadata or {}
        }
        
        # Save to Weaviate
        client.data_object.create(data_obj, class_name=namespace, vector=vector)
        logger.info(f"Successfully saved to memory: {namespace}/{key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save to memory: {e}")
        return False

def query_memory(namespace: str, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Query memory using vector similarity search.
    
    Args:
        namespace: Memory namespace/class name
        query_text: Text to search for
        top_k: Number of results to return
        
    Returns:
        List of matching memory entries
    """
    if not client or not embedder:
        logger.warning("Memory query not available - missing Weaviate or sentence transformers")
        return []
    
    try:
        # Generate query vector
        vector = embedder.encode(query_text)
        
        # Query Weaviate
        result = client.query.get(namespace, ["key", "content", "metadata"])\
                         .with_near_vector({"vector": vector.tolist()})\
                         .with_limit(top_k).do()
        
        # Extract results
        if "data" in result and "Get" in result["data"]:
            return result["data"]["Get"][namespace]
        else:
            return []
            
    except Exception as e:
        logger.error(f"Failed to query memory: {e}")
        return []

def is_memory_available() -> bool:
    """Check if memory system is fully available."""
    return client is not None and embedder is not None

def get_memory_status() -> Dict[str, Any]:
    """Get status of memory system components."""
    return {
        "weaviate_available": WEAVIATE_AVAILABLE,
        "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
        "client_initialized": client is not None,
        "embedder_initialized": embedder is not None,
        "fully_available": is_memory_available(),
        "weaviate_url": WEAVIATE_URL is not None,
        "weaviate_api_key": WEAVIATE_API_KEY is not None
    }