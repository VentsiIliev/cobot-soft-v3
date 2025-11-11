"""
Mixin classes and base widgets that provide automatic translation capabilities.
"""
from typing import Union, Optional, Any
from PyQt6.QtWidgets import QWidget, QDialog, QFrame
from modules.shared.localization.enums.Message import Message
from .container import get_app_translator
from .translator import AppTranslator

class TranslatableMixin:
    """
    Mixin that adds translation capabilities to any class.
    Automatically handles language change updates.
    """
    
    def __init_translation__(self, translator: Optional[AppTranslator] = None):
        """
        Initialize translation capabilities.
        Should be called in the __init__ of the class using this mixin.
        
        Args:
            translator: Optional translator instance (uses global if None)
        """
        self.translator = translator or get_app_translator()
        
        # Connect to language change signals for automatic updates
        self.translator.language_changed.connect(self._on_language_changed)
        
        # Flag to prevent recursive calls during initialization
        self._translation_initialized = True
    
    def tr(self, key: Union[str, Message], **params) -> str:
        """
        Convenient translation method.
        
        Args:
            key: Translation key
            **params: Parameters for string formatting
            
        Returns:
            Translated string
        """
        return self.translator.get(key, **params)
    
    def _on_language_changed(self) -> None:
        """
        Handle language change notifications.
        Calls retranslate() if it exists and translation is initialized.
        """
        if hasattr(self, '_translation_initialized') and hasattr(self, 'retranslate'):
            self.retranslate()
    
    def retranslate(self) -> None:
        """
        Override this method in subclasses to update translations.
        Called automatically when language changes.
        """
        pass


class TranslatableQFrame(QFrame, TranslatableMixin):
    """
    QFrame base class with automatic translation capabilities.

    Usage:
        class MyFrame(TranslatableQFrame):
            def __init__(self, parent=None):
                super().__init__(parent, auto_retranslate=False)
                self.setup_ui()
                self.init_translations()  # Call this after UI setup

            def setup_ui(self):
                self.label = QLabel()
                # UI setup code...
            def retranslate(self):
                self.label.setText(self.tr(TranslationKeys.SOME_KEY))
    """

    def __init__(self, parent: Optional[QWidget] = None, translator: Optional[AppTranslator] = None,
                 auto_retranslate: bool = True):
        QFrame.__init__(self, parent)
        TranslatableMixin.__init_translation__(self,translator)

        if auto_retranslate and hasattr(self, 'retranslate'):
            self.retranslate()

    def tr(self, key, **params):
        """
        Custom translation method that overrides QFrame.tr().
        This ensures our translation system is used instead of PyQt's.
        """
        return self.translator.get(key, **params)

    def init_translations(self):
        """Call this after UI setup to initialize translations."""
        if hasattr(self, 'retranslate'):
            self.retranslate()


class TranslatableWidget(QWidget, TranslatableMixin):
    """
    QWidget base class with automatic translation capabilities.
    
    Usage:
        class MyWidget(TranslatableWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setup_ui()
                self.init_translations()  # Call this after UI setup
                
            def setup_ui(self):
                self.button = QPushButton()
                # UI setup code...
                
            def retranslate(self):
                self.button.setText(self.tr(TranslationKeys.LOGIN))
    """
    
    def __init__(self, parent: Optional[QWidget] = None, translator: Optional[AppTranslator] = None, auto_retranslate: bool = True):
        QWidget.__init__(self, parent)
        TranslatableMixin.__init_translation__(self, translator)
        
        # Only call retranslate automatically if requested and method exists
        if auto_retranslate and hasattr(self, 'retranslate'):
            self.retranslate()
    
    def tr(self, key, **params):
        """
        Custom translation method that overrides QWidget.tr().
        This ensures our translation system is used instead of PyQt's.
        """
        return self.translator.get(key, **params)
    
    def init_translations(self):
        """Call this after UI setup to initialize translations."""
        if hasattr(self, 'retranslate'):
            self.retranslate()


class TranslatableDialog(QDialog, TranslatableMixin):
    """
    QDialog base class with automatic translation capabilities.
    
    Usage:
        class MyDialog(TranslatableDialog):
            def __init__(self, parent=None):
                super().__init__(parent, auto_retranslate=False)
                self.setup_ui()
                self.init_translations()  # Call this after UI setup
                
            def setup_ui(self):
                self.ok_button = QPushButton()
                # UI setup code...
                
            def retranslate(self):
                self.ok_button.setText(self.tr(TranslationKeys.OK))
    """
    
    def __init__(self, parent: Optional[QWidget] = None, translator: Optional[AppTranslator] = None, auto_retranslate: bool = True):
        QDialog.__init__(self, parent)
        TranslatableMixin.__init_translation__(self, translator)
        
        # Only call retranslate automatically if requested and method exists
        if auto_retranslate and hasattr(self, 'retranslate'):
            self.retranslate()
    
    def tr(self, key, **params):
        """
        Custom translation method that overrides QDialog.tr().
        This ensures our translation system is used instead of PyQt's.
        """
        return self.translator.get(key, **params)
    
    def init_translations(self):
        """Call this after UI setup to initialize translations."""
        if hasattr(self, 'retranslate'):
            self.retranslate()


class TranslatableObject(TranslatableMixin):
    """
    Pure mixin for non-widget classes that need translation capabilities.
    
    Usage:
        class MyService(TranslatableObject):
            def __init__(self):
                super().__init__()
                self.__init_translation__()
                
            def get_error_message(self):
                return self.tr(TranslationKeys.ERROR_MESSAGE)
    """
    
    def __init__(self, translator: Optional[AppTranslator] = None):
        TranslatableMixin.__init_translation__(self, translator)