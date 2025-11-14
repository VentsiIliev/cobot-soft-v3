"""
Translatable widget variants for common UI components.
"""
from typing import Optional
from frontend.pl_ui.ui.widgets.Drawer import Drawer
from .mixins import TranslatableMixin
from .translator import AppTranslator


class TranslatableDrawer(Drawer, TranslatableMixin):
    """
    Drawer widget with automatic translation capabilities.
    Properly handles initialization order to avoid MRO issues.
    """
    
    def __init__(self, parent=None, animation_duration=300, side="right", translator: Optional[AppTranslator] = None):
        # Initialize Drawer first with all its parameters
        Drawer.__init__(self, parent, animation_duration, side)
        
        # Initialize translation capabilities but DON'T call retranslate yet
        TranslatableMixin.__init_translation__(self, translator)
        
        # Set a flag to indicate translation is ready
        self._translation_ready = False
    
    def tr(self, key, **params):
        """
        Custom translation method that overrides QWidget.tr().
        This ensures our translation system is used instead of PyQt's.
        """
        return self.translator.get(key, **params)
    
    def init_translations(self):
        """
        Call this after UI setup to initialize translations.
        This ensures all UI elements exist before retranslate() is called.
        """
        self._translation_ready = True
        if hasattr(self, 'retranslate'):
            self.retranslate()
    
    def _on_language_changed(self) -> None:
        """
        Handle language change notifications.
        Only call retranslate if translations are ready.
        """
        if hasattr(self, '_translation_ready') and self._translation_ready and hasattr(self, 'retranslate'):
            self.retranslate()