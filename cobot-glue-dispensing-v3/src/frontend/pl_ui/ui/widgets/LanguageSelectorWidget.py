from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import pyqtSignal

from src.frontend.pl_ui.localization import get_app_translator, Language


class LanguageSelectorWidget(QComboBox):
    languageChanged = pyqtSignal(Language)

    def __init__(self, parent=None):
        super().__init__(parent)
        # set object name for styling
        self.translator = get_app_translator()
        
        # Connect to language changes for automatic updates
        self.translator.language_changed.connect(self.updateSelectedLang)
        
        self.languages = list(Language)
        self.language_name_to_enum = {lang.display_name: lang for lang in self.languages}

        # Populate dropdown
        self.addItems([lang.display_name for lang in self.languages])

        # Set current language
        self.updateSelectedLang()

        self.currentIndexChanged.connect(self._on_language_change)

    def _on_language_change(self, index):
        selected_text = self.currentText()
        selected_enum = self.language_name_to_enum[selected_text]
        self.translator.set_language(selected_enum)
        self.languageChanged.emit(selected_enum)

    def updateSelectedLang(self):
        current_lang = self.translator.current_language
        self.setCurrentIndex(self.findText(current_lang.display_name))


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = LanguageSelectorWidget()
    widget.show()


    def on_language_change(lang):
        print(f"Language changed to: {lang.display_name}")


    widget.languageChanged.connect(on_language_change)

    sys.exit(app.exec())
