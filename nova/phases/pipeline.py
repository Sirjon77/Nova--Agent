"""
Advanced Pipeline for Nova Agent

This module orchestrates the complete processing pipeline:
- Analysis with advanced NLP
- Planning with context awareness
- Execution with parameter validation
- Response formatting with metadata
"""

import time
import logging
from typing import Dict, Any, Tuple, Generator, Union
from .analyze_phase import analyze
from .plan_phase import plan
from .execute_phase import execute
from .respond_phase import respond

logger = logging.getLogger(__name__)

def run_phases(message: str, stream: bool = False) -> Union[str, Generator[Tuple[str, Any], None, None]]:
    """
    Run the complete processing pipeline
    
    Args:
        message: User input message
        stream: Whether to stream results back to client
        
    Returns:
        Final response string or generator for streaming
    """
    if stream:
        return _run_phases_stream(message)
    else:
        return _run_phases_non_stream(message)

def _run_phases_stream(message: str) -> Generator[Tuple[str, Any], None, None]:
    """Internal streaming implementation"""
    start_time = time.time()
    
    try:
        # Phase 1: Analysis
        analysis_start = time.time()
        analysis = analyze(message)
        analysis_time = time.time() - analysis_start
        
        yield "analysis", {
            "result": analysis,
            "execution_time": analysis_time,
            "phase": "analysis"
        }
        
        # Phase 2: Planning
        planning_start = time.time()
        plan_obj = plan(analysis)
        planning_time = time.time() - planning_start
        
        yield "plan", {
            "result": plan_obj,
            "execution_time": planning_time,
            "phase": "planning"
        }
        
        # Phase 3: Execution
        execution_start = time.time()
        result = execute(plan_obj)
        execution_time = time.time() - execution_start
        
        yield "execute", {
            "result": result,
            "execution_time": execution_time,
            "phase": "execution"
        }
        
        # Phase 4: Response
        response_start = time.time()
        
        # Prepare metadata for response formatting
        metadata = {
            "confidence": analysis.get("confidence", 0.0),
            "classification_method": analysis.get("classification_method", ""),
            "intent": analysis.get("intent", ""),
            "entities": analysis.get("entities", {}),
            "context": analysis.get("context", {}),
            "execution_time": time.time() - start_time,
            "phase_times": {
                "analysis": analysis_time,
                "planning": planning_time,
                "execution": execution_time
            }
        }
        
        final_response = respond(result, metadata)
        response_time = time.time() - response_start
        
        yield "final", {
            "result": final_response,
            "execution_time": response_time,
            "phase": "response",
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        error_response = f"❌ Pipeline error: {str(e)}"
        
        yield "error", {
            "result": error_response,
            "error": str(e),
            "phase": "error"
        }

def _run_phases_non_stream(message: str) -> str:
    """Internal non-streaming implementation"""
    start_time = time.time()
    
    try:
        # Phase 1: Analysis
        analysis_start = time.time()
        analysis = analyze(message)
        analysis_time = time.time() - analysis_start
        
        # Phase 2: Planning
        planning_start = time.time()
        plan_obj = plan(analysis)
        planning_time = time.time() - planning_start
        
        # Phase 3: Execution
        execution_start = time.time()
        result = execute(plan_obj)
        execution_time = time.time() - execution_start
        
        # Phase 4: Response
        time.time()
        
        # Prepare metadata for response formatting
        metadata = {
            "confidence": analysis.get("confidence", 0.0),
            "classification_method": analysis.get("classification_method", ""),
            "intent": analysis.get("intent", ""),
            "entities": analysis.get("entities", {}),
            "context": analysis.get("context", {}),
            "execution_time": time.time() - start_time,
            "phase_times": {
                "analysis": analysis_time,
                "planning": planning_time,
                "execution": execution_time
            }
        }
        
        final_response = respond(result, metadata)
        
        return final_response
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        error_response = f"❌ Pipeline error: {str(e)}"
        
        return error_response

def run_phases_with_metrics(message: str) -> Dict[str, Any]:
    """
    Run phases with detailed metrics and timing
    
    Args:
        message: User input message
        
    Returns:
        Dictionary with results and metrics
    """
    start_time = time.time()
    
    try:
        # Run all phases
        analysis = analyze(message)
        plan_obj = plan(analysis)
        result = execute(plan_obj)
        
        # Prepare metadata
        metadata = {
            "confidence": analysis.get("confidence", 0.0),
            "classification_method": analysis.get("classification_method", ""),
            "intent": analysis.get("intent", ""),
            "entities": analysis.get("entities", {}),
            "context": analysis.get("context", {})
        }
        
        final_response = respond(result, metadata)
        
        return {
            "success": True,
            "response": final_response,
            "analysis": analysis,
            "plan": plan_obj,
            "execution_result": result,
            "metadata": metadata,
            "total_time": time.time() - start_time
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time": time.time() - start_time
        }

# Legacy compatibility function
def run_phases_legacy(message: str, stream: bool = False):
    """
    Legacy pipeline function for backward compatibility
    """
    return run_phases(message, stream)
