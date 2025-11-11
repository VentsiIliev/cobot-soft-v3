"""
Dependency injection container for localization services.
Provides singleton access to the translation system.
"""
from typing import Optional
from modules.shared.localization.enums.Language import  Language
from .translator import AppTranslator

# Global singleton instance
_app_translator: Optional[AppTranslator] = None


def get_app_translator() -> AppTranslator:
    """
    Get the singleton translator instance.
    
    Returns:
        AppTranslator: The global translator instance
    """
    global _app_translator
    if _app_translator is None:
        _app_translator = AppTranslator()
    return _app_translator


def setup_localization(initial_language: Optional[Language] = None) -> AppTranslator:
    """
    Initialize the localization system.
    Should be called once at application startup.
    
    Args:
        initial_language: Optional language to set initially
        
    Returns:
        AppTranslator: The initialized translator instance
    """
    translator = get_app_translator()
    
    if initial_language:
        translator.set_language(initial_language)
    
    return translator


def reset_localization() -> None:
    """
    Reset the localization system.
    Useful for testing or when reinitializing the application.
    """
    global _app_translator
    _app_translator = None


# Convenience function for quick translation access
def tr(key, **params) -> str:
    """
    Quick translation function.
    
    Args:
        key: Translation key
        **params: Parameters for formatting
        
    Returns:
        Translated string
    """
    return get_app_translator().get(key, **params)