"""
Global application state
Stores heavy resources loaded at startup (OCR engine, LLM service, etc.)
"""

class AppState:
    """Application-wide state container"""
    ocr_service = None  # Will be initialized in lifespan
    llm_service = None  # Shared LLM service with single MemorySaver instance
