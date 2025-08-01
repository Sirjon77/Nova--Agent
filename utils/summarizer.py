"""
Enhanced Summarizer for Nova Agent

This module provides advanced text summarization capabilities:
- Recursive summarization for long texts
- Context-aware summarization
- Format handling and token management
- Error handling and user feedback
"""

import re
import logging
from typing import Optional, Dict, Any, List
from utils.openai_wrapper import chat_completion
from utils.memory_manager import memory_manager

logger = logging.getLogger(__name__)

class EnhancedSummarizer:
    """
    Enhanced summarizer with recursive summarization and context handling.
    
    Features:
    - Recursive summarization for long texts
    - Context-aware prompts
    - Token limit management
    - Format handling
    - Error recovery
    """
    
    def __init__(self, 
                 max_chunk_size: int = 3000,
                 max_summary_length: int = 500,
                 model: str = "gpt-4o-mini"):
        """
        Initialize the enhanced summarizer.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            max_summary_length: Maximum tokens for summary
            model: OpenAI model to use
        """
        self.max_chunk_size = max_chunk_size
        self.max_summary_length = max_summary_length
        self.model = model
        
        logger.info(f"EnhancedSummarizer initialized with model: {model}")
    
    def summarize_text(self, 
                      text: str, 
                      title: Optional[str] = None,
                      source: Optional[str] = None,
                      context: Optional[str] = None) -> str:
        """
        Summarize text with enhanced features.
        
        Args:
            text: Text to summarize
            title: Optional title for context
            source: Optional source URL/identifier
            context: Optional additional context
            
        Returns:
            str: Generated summary
        """
        try:
            # Clean and prepare text
            text = self._clean_text(text)
            
            if not text.strip():
                return "No content to summarize."
            
            # Handle long texts with recursive summarization
            if len(text) > self.max_chunk_size * 2:
                return self._recursive_summarize(text, title, source, context)
            else:
                return self._single_summarize(text, title, source, context)
                
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Sorry, I cannot summarize this content right now. Error: {str(e)}"
    
    def _recursive_summarize(self, 
                           text: str, 
                           title: Optional[str] = None,
                           source: Optional[str] = None,
                           context: Optional[str] = None) -> str:
        """
        Recursively summarize long text by chunking and summarizing summaries.
        
        Args:
            text: Long text to summarize
            title: Optional title
            source: Optional source
            context: Optional context
            
        Returns:
            str: Final summary
        """
        try:
            # Split text into chunks
            chunks = self._split_text_into_chunks(text)
            logger.info(f"Split text into {len(chunks)} chunks for recursive summarization")
            
            # Summarize each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                chunk_title = f"{title} (Part {i+1})" if title else f"Part {i+1}"
                summary = self._single_summarize(chunk, chunk_title, source, context)
                chunk_summaries.append(summary)
            
            # If we have multiple summaries, summarize them together
            if len(chunk_summaries) > 1:
                combined_summaries = "\n\n".join(chunk_summaries)
                final_summary = self._single_summarize(
                    combined_summaries, 
                    title, 
                    source, 
                    f"Combined summary of {len(chunks)} parts"
                )
                return final_summary
            else:
                return chunk_summaries[0]
                
        except Exception as e:
            logger.error(f"Recursive summarization failed: {e}")
            return f"Failed to summarize long content: {str(e)}"
    
    def _single_summarize(self, 
                         text: str, 
                         title: Optional[str] = None,
                         source: Optional[str] = None,
                         context: Optional[str] = None) -> str:
        """
        Summarize a single chunk of text.
        
        Args:
            text: Text to summarize
            title: Optional title
            source: Optional source
            context: Optional context
            
        Returns:
            str: Summary
        """
        try:
            # Build context-aware prompt
            prompt = self._build_summarization_prompt(text, title, source, context)
            
            # Generate summary
            response = chat_completion(
                prompt,
                model=self.model,
                max_tokens=self.max_summary_length,
                temperature=0.3
            )
            
            # Clean and format response
            summary = self._clean_summary(response)
            
            # Log successful summarization
            logger.info(f"Successfully summarized {len(text)} chars to {len(summary)} chars")
            
            return summary
            
        except Exception as e:
            logger.error(f"Single summarization failed: {e}")
            return f"Failed to summarize content: {str(e)}"
    
    def _build_summarization_prompt(self, 
                                  text: str, 
                                  title: Optional[str] = None,
                                  source: Optional[str] = None,
                                  context: Optional[str] = None) -> str:
        """
        Build a context-aware summarization prompt.
        
        Args:
            text: Text to summarize
            title: Optional title
            source: Optional source
            context: Optional context
            
        Returns:
            str: Formatted prompt
        """
        system_prompt = "You are an expert summarizer. Create concise, accurate summaries that capture the key points and main ideas."
        
        # Build context information
        context_info = []
        if title:
            context_info.append(f"Title: {title}")
        if source:
            context_info.append(f"Source: {source}")
        if context:
            context_info.append(f"Context: {context}")
        
        context_str = "\n".join(context_info) if context_info else ""
        
        # Build user prompt
        user_prompt = f"""Please summarize the following content concisely and accurately.

{context_str}

Content to summarize:
{text}

Summary:"""
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into manageable chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Try to split on paragraph boundaries first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= self.max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we still have chunks that are too large, split on sentences
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.max_chunk_size:
                final_chunks.append(chunk)
            else:
                # Split on sentences
                sentences = re.split(r'[.!?]+', chunk)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            final_chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
        
        return final_chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and prepare text for summarization.
        
        Args:
            text: Raw text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _clean_summary(self, summary: str) -> str:
        """
        Clean and format the generated summary.
        
        Args:
            summary: Raw summary from API
            
        Returns:
            str: Cleaned summary
        """
        # Remove markdown code blocks if present
        summary = re.sub(r'```.*?```', '', summary, flags=re.DOTALL)
        
        # Remove leading/trailing whitespace
        summary = summary.strip()
        
        # Ensure it ends with proper punctuation
        if summary and not summary[-1] in '.!?':
            summary += '.'
        
        return summary
    
    def summarize_web_content(self, 
                            url: str, 
                            title: str, 
                            content: str,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Summarize web content and store in memory.
        
        Args:
            url: Source URL
            title: Page title
            content: Page content
            metadata: Optional metadata
            
        Returns:
            str: Generated summary
        """
        try:
            # Generate summary
            summary = self.summarize_text(content, title, url, "Web content")
            
            # Store in memory
            memory_manager.add_summary(url, title, summary, metadata)
            
            return summary
            
        except Exception as e:
            logger.error(f"Web content summarization failed: {e}")
            return f"Failed to summarize web content: {str(e)}"
    
    def get_summarization_stats(self) -> Dict[str, Any]:
        """Get summarization statistics."""
        try:
            status = memory_manager.get_memory_status()
            return {
                "model": self.model,
                "max_chunk_size": self.max_chunk_size,
                "max_summary_length": self.max_summary_length,
                "summary_count": status.get("summary_count", 0),
                "memory_status": status
            }
        except Exception as e:
            logger.error(f"Failed to get summarization stats: {e}")
            return {"error": str(e)}

# Global summarizer instance
enhanced_summarizer = EnhancedSummarizer()

# Convenience functions for backward compatibility
def summarize_text(text: str, title: Optional[str] = None, source: Optional[str] = None) -> str:
    """Summarize text using enhanced summarizer."""
    return enhanced_summarizer.summarize_text(text, title, source)

def summarize_web_content(url: str, title: str, content: str) -> str:
    """Summarize web content using enhanced summarizer."""
    return enhanced_summarizer.summarize_web_content(url, title, content) 