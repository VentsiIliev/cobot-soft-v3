import json
from pathlib import Path
from modules.shared.localization.enums.Language import Language
from modules.shared.MessageBroker import MessageBroker
# Resolve the base directory of this file
BASE_DIR = Path(__file__).resolve().parent

# Construct relative paths
SETTINGS_PATH = BASE_DIR.parent.parent / "system" / "storage" / "ui_settings" / "ui_settings.json"
LANGUAGES_DIR = BASE_DIR / "languages"  # assuming this file is inside shared/localization/

class LanguageResourceLoader:
    _instance = None

    def __new__(cls, language: Language = None):
        if cls._instance is None:
            cls._instance = super(LanguageResourceLoader, cls).__new__(cls)
            cls._instance._init(language)
        return cls._instance

    def _init(self, language: Language = None):
        self.language = language or self._load_language_from_settings()
        self._load_language_data()

    def _load_language_from_settings(self) -> Language:
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lang_str = data.get("Language", "English")
                return Language[lang_str.upper()]
        except Exception as e:
            print(f"Failed to load language setting: {e}")
            return Language.ENGLISH

    def _load_language_data(self):
        lang_file = LANGUAGES_DIR / f"{self.language.filename_key}.json"
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Language file not found: {lang_file}")
            self.data = {}

    def updateLanguage(self, language: Language):

        self.language = language
        self._load_language_data()
        self._save_language_to_settings()
        broker = MessageBroker()
        broker.publish("Language", "Change")

    def _save_language_to_settings(self):
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Load existing settings if present
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            # Only update the language key
            settings["Language"] = self.language.filename_key
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save language setting: {e}")

    def get_message(self, message):
        return self.data['Message'][message.name]

    def get_prompt(self, prompt):
        return self.data['Message'][prompt]

    def getButtonLabel(self, buttonLabel):
        return self.data['ButtonLabel'][buttonLabel.name]


# Example usage
if __name__ == "__main__":
    from enums.Message import Message
    loader = LanguageResourceLoader()
    print("Current language:", loader.language)
    print(loader.get_message(Message.MESSAGE_CAPTURE_FAILED))
