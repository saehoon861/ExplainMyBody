"""
Global application state
Stores heavy resources loaded at startup (OCR engine, etc.)
"""

class AppState:
    """Application-wide state container"""
    ocr_service = None  # Will be initialized in lifespan
