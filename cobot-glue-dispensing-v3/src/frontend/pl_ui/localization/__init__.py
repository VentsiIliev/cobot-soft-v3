"""
Improved localization system for the pl_ui package.

This module provides a clean, centralized way to handle translations
across the entire UI application.

Usage:
    # At application startup
    from pl_ui.localization import setup_localization
    setup_localization()
    
    # In widgets
    from pl_ui.localization import TranslatableWidget, TranslationKeys
    
    class MyWidget(TranslatableWidget):
        def retranslate(self):
            self.button.setText(self.tr(TranslationKeys.Auth.LOGIN))
    
    # For quick translations
    from pl_ui.localization import tr
    text = tr(TranslationKeys.Dashboard.START)
"""

# Core functionality
from .container import (
    get_app_translator,
    setup_localization,
    reset_localization,
    tr
)

from .translator import AppTranslator

from .mixins import (
    TranslatableMixin,
    TranslatableWidget, 
    TranslatableDialog,
    TranslatableObject
)

from .widgets import (
    TranslatableDrawer,
)

from .keys import TranslationKeys

# Convenience imports for backwards compatibility
from modules.shared.localization.enums.Language import Language
from modules.shared.localization.enums.Message import Message

__all__ = [
    # Core services
    'AppTranslator',
    'get_app_translator', 
    'setup_localization',
    'reset_localization',
    'tr',
    
    # Base classes and mixins
    'TranslatableMixin',
    'TranslatableWidget',
    'TranslatableDialog', 
    'TranslatableObject',
    
    # Specialized widgets
    'TranslatableDrawer',
    
    # Translation keys
    'TranslationKeys',
    
    # Enums (re-exported for convenience)
    'Language',
    'Message',
]