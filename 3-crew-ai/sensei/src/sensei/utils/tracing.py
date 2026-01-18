"""LangSmith tracing integration for CrewAI.

This module sets up OpenTelemetry instrumentation to send traces
from CrewAI and OpenAI to LangSmith for observability.

IMPORTANT: This module must be imported and `setup_tracing()` called
BEFORE importing any CrewAI modules to ensure proper instrumentation.

Environment Variables Required:
    LANGSMITH_API_KEY: Your LangSmith API key
    LANGSMITH_PROJECT: Project name in LangSmith (e.g., "project-sensei")
    
Optional Environment Variables:
    LANGSMITH_TRACING: Set to "true" to enable (default: true if API key exists)
    LANGSMITH_ENDPOINT: API endpoint (default: https://api.smith.langchain.com)
    LANGCHAIN_TRACING_V2: Alternative tracing flag (default: true)

Usage:
    # At the very start of your application (before CrewAI imports):
    from sensei.utils.tracing import setup_tracing
    setup_tracing()
    
    # Now you can import and use CrewAI
    from sensei.crews import CurriculumCrew
"""

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Track if tracing has been initialized
_tracing_initialized = False


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing should be enabled.
    
    Returns:
        True if tracing is enabled and API key is set.
    """
    api_key = os.environ.get("LANGSMITH_API_KEY")
    tracing_flag = os.environ.get("LANGSMITH_TRACING", "").lower()
    langchain_flag = os.environ.get("LANGCHAIN_TRACING_V2", "").lower()
    
    # Tracing is enabled if:
    # 1. API key exists AND
    # 2. Either LANGSMITH_TRACING=true or LANGCHAIN_TRACING_V2=true (or neither set, default on)
    has_api_key = bool(api_key and api_key.strip())
    tracing_on = tracing_flag in ("true", "1", "") or langchain_flag in ("true", "1")
    
    return has_api_key and tracing_on


def setup_tracing(force: bool = False) -> bool:
    """Initialize LangSmith tracing for CrewAI.
    
    This function sets up OpenTelemetry instrumentation to capture
    traces from CrewAI and OpenAI, sending them to LangSmith.
    
    Args:
        force: If True, re-initialize even if already initialized.
    
    Returns:
        True if tracing was successfully initialized, False otherwise.
    
    Note:
        This function should be called BEFORE importing any CrewAI modules.
        It's safe to call multiple times (will no-op after first call).
    """
    global _tracing_initialized
    
    if _tracing_initialized and not force:
        logger.debug("Tracing already initialized, skipping.")
        return True
    
    if not is_tracing_enabled():
        logger.info(
            "LangSmith tracing disabled. "
            "Set LANGSMITH_API_KEY and LANGSMITH_TRACING=true to enable."
        )
        return False
    
    try:
        # Ensure LANGCHAIN_TRACING_V2 is set (some libraries check this)
        if not os.environ.get("LANGCHAIN_TRACING_V2"):
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        
        # Import tracing dependencies
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from langsmith.integrations.otel import OtelSpanProcessor
        from openinference.instrumentation.crewai import CrewAIInstrumentor
        from openinference.instrumentation.openai import OpenAIInstrumentor
        
        # Setup tracer provider if not already set
        current_provider = trace.get_tracer_provider()
        if not isinstance(current_provider, TracerProvider):
            tracer_provider = TracerProvider()
            trace.set_tracer_provider(tracer_provider)
        else:
            tracer_provider = current_provider
        
        # Register LangSmith as a span processor
        tracer_provider.add_span_processor(OtelSpanProcessor())
        
        # Instrument CrewAI and OpenAI
        CrewAIInstrumentor().instrument()
        OpenAIInstrumentor().instrument()
        
        _tracing_initialized = True
        
        project = os.environ.get("LANGSMITH_PROJECT", "default")
        logger.info(f"LangSmith tracing initialized for project: {project}")
        
        return True
        
    except ImportError as e:
        logger.warning(
            f"Could not initialize LangSmith tracing (missing dependency): {e}. "
            "Install with: pip install langsmith openinference-instrumentation-crewai "
            "openinference-instrumentation-openai opentelemetry-sdk"
        )
        return False
    except Exception as e:
        logger.warning(f"Failed to initialize LangSmith tracing: {e}")
        return False


def get_tracing_status() -> dict[str, Any]:
    """Get current tracing configuration status.
    
    Returns:
        Dictionary with tracing status information.
    """
    return {
        "initialized": _tracing_initialized,
        "enabled": is_tracing_enabled(),
        "api_key_set": bool(os.environ.get("LANGSMITH_API_KEY")),
        "project": os.environ.get("LANGSMITH_PROJECT", "default"),
        "endpoint": os.environ.get(
            "LANGSMITH_ENDPOINT", 
            "https://api.smith.langchain.com"
        ),
        "langsmith_tracing": os.environ.get("LANGSMITH_TRACING", "not set"),
        "langchain_tracing_v2": os.environ.get("LANGCHAIN_TRACING_V2", "not set"),
    }
