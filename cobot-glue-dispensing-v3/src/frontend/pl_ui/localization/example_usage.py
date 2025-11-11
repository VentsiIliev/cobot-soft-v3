"""
Examples showing how to use the new localization system.
This file demonstrates various usage patterns and migration strategies.
"""

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel

from modules.shared.localization.LanguageResourceLoader import LanguageResourceLoader
from src.frontend.pl_ui.localization import (
    setup_localization,
    TranslatableWidget,
    TranslationKeys,
    Language,
    tr
)


# Example 1: Simple translatable widget
class SimpleWidget(TranslatableWidget):
    """Basic example of a translatable widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel()
        self.login_button = QPushButton()
        self.start_button = QPushButton()
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.login_button)
        layout.addWidget(self.start_button)
    
    def retranslate(self):
        """Called automatically when language changes."""
        self.title_label.setText(self.tr(TranslationKeys.Navigation.WORK))
        self.login_button.setText(self.tr(TranslationKeys.Auth.LOGIN))
        self.start_button.setText(self.tr(TranslationKeys.Dashboard.START))


# Example 2: Widget with language switcher
class LanguageSwitcherWidget(TranslatableWidget):
    """Widget that demonstrates language switching."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.welcome_label = QLabel()
        
        # Language switch buttons
        self.english_btn = QPushButton("English")
        self.spanish_btn = QPushButton("Español") 
        self.french_btn = QPushButton("Français")
        
        self.english_btn.clicked.connect(lambda: self.translator.set_language(Language.ENGLISH))
        self.spanish_btn.clicked.connect(lambda: self.translator.set_language(Language.SPANISH))
        self.french_btn.clicked.connect(lambda: self.translator.set_language(Language.FRENCH))
        
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.english_btn)
        layout.addWidget(self.spanish_btn) 
        layout.addWidget(self.french_btn)
    
    def retranslate(self):
        """Update translations - called automatically on language change."""
        self.welcome_label.setText(self.tr(TranslationKeys.Auth.LOGIN))


# Example 3: Migration comparison
class OldStyleWidget(QWidget):
    """OLD WAY: Manual localization handling (DON'T USE)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # OLD: Manual imports and setup
        from modules.shared.localization.LanguageResourceLoader import LanguageResourceLoader
        from modules.shared.localization.enums.Message import Message
        from modules.shared.MessageBroker import MessageBroker
        
        self.lang_loader = LanguageResourceLoader()  # Creates instance
        
        # OLD: Manual broker subscription
        broker = MessageBroker()
        broker.subscribe("Language", self.update_translations)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # OLD: Set text immediately with manual calls
        from modules.shared.localization.enums.Message import Message
        self.label = QLabel(self.lang_loader.get_message(Message.LOGIN))
        layout.addWidget(self.label)
    
    def update_translations(self, _):
        """OLD: Manual translation updates."""
        from modules.shared.localization.enums.Message import Message
        self.lang_loader = LanguageResourceLoader()  # Recreate instance!
        self.label.setText(self.lang_loader.get_message(Message.LOGIN))


class NewStyleWidget(TranslatableWidget):
    """NEW WAY: Clean automatic localization (RECOMMENDED)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)  # Automatic setup!
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.label = QLabel()  # No text set here
        layout.addWidget(self.label)
    
    def retranslate(self):
        """NEW: Clean automatic updates."""
        self.label.setText(self.tr(TranslationKeys.Auth.LOGIN))


# Example 4: Non-widget class with translations
from src.frontend.pl_ui.localization import TranslatableObject

class ServiceWithTranslations(TranslatableObject):
    """Example of non-widget class that needs translations."""
    
    def __init__(self):
        super().__init__()
    
    def get_status_message(self, is_ready: bool) -> str:
        if is_ready:
            return self.tr(TranslationKeys.Status.READY)
        else:
            return self.tr(TranslationKeys.Status.UNKNOWN)
    
    def get_welcome_message(self, username: str) -> str:
        # Future: Could support parameters
        # return self.tr("WELCOME_USER", username=username)
        return f"Welcome, {username}!"


# Example application
def main():
    """Example application demonstrating the new localization system."""
    app = QApplication([])
    
    # IMPORTANT: Initialize localization at app startup
    setup_localization(Language.ENGLISH)
    
    # Create and show widgets - they automatically translate!
    window = SimpleWidget()
    window.setWindowTitle("Localization Example")
    window.resize(300, 200)
    window.show()
    
    # Language switcher window
    switcher = LanguageSwitcherWidget()
    switcher.setWindowTitle("Language Switcher")
    switcher.move(350, 0)
    switcher.show()
    
    # Quick translation without widgets
    print(f"Quick translation: {tr(TranslationKeys.Dashboard.START)}")
    
    app.exec()


if __name__ == "__main__":
    main()