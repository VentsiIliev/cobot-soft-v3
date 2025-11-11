"""
Centralized translation service for the application.
Provides a clean interface between UI components and the localization system.
"""
from typing import Union, Any
from PyQt6.QtCore import QObject, pyqtSignal

from  modules.shared.localization.LanguageResourceLoader import LanguageResourceLoader
from  modules.shared.localization.enums.Language import Language
from modules.shared.localization.enums.Message import Message


class AppTranslator(QObject):
    """
    Single point of truth for all translations in the application.
    Wraps the shared's LanguageResourceLoader and provides a cleaner interface.
    """
    
    # Signal emitted when language changes
    language_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._loader = LanguageResourceLoader()
        self._current_language = self._loader.language
        
        # Subscribe to language changes from the underlying system
        from modules.shared.MessageBroker import MessageBroker
        broker = MessageBroker()
        broker.subscribe("Language", self._on_language_changed)
    
    def get(self, key: Union[str, Message], **params) -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key (Message enum or string)
            **params: Parameters for string formatting (future enhancement)
            
        Returns:
            Translated string
        """
        try:
            if isinstance(key, Message):
                return self._loader.get_message(key)
            elif isinstance(key, str):
                # For backwards compatibility, try to get by string name
                message_enum = getattr(Message, key, None)
                if message_enum:
                    return self._loader.get_message(message_enum)
                return key  # Return the key itself if not found
            else:
                return str(key)
        except Exception as e:
            print(f"Translation error for key '{key}': {e}")
            return str(key)  # Fallback to key itself
    
    def set_language(self, language: Language) -> None:
        """
        Change the application language.
        
        Args:
            language: New language to use
        """
        if language != self._current_language:
            self._loader.updateLanguage(language)
            self._current_language = language
            # Note: language_changed signal will be emitted by _on_language_changed
    
    @property
    def current_language(self) -> Language:
        """Get the currently active language."""
        return self._current_language
    
    def _on_language_changed(self, _message: Any = None) -> None:
        """
        Handle language change notifications from MessageBroker.
        
        Args:
            _message: Message from broker (unused)
        """
        old_language = self._current_language
        self._current_language = self._loader.language
        
        if old_language != self._current_language:
            self.language_changed.emit()
    
    def get_available_languages(self) -> list[Language]:
        """
        Get list of available languages.
        
        Returns:
            List of available Language enum values
        """
        return list(Language)
    
    # Convenience methods for commonly used translations
    def get_button_label(self, button_label) -> str:
        """Get translated button label."""
        try:
            return self._loader.getButtonLabel(button_label)
        except Exception as e:
            print(f"Button label translation error: {e}")
            return str(button_label)
    
    def get_prompt(self, prompt: str) -> str:
        """Get translated prompt."""
        try:
            return self._loader.get_prompt(prompt)
        except Exception as e:
            print(f"Prompt translation error: {e}")
            return prompt