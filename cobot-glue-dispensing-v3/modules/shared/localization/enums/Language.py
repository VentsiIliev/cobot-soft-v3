from enum import Enum


class Language(Enum):
    BULGARIAN = ("Български", "bulgarian")
    ENGLISH = ("English", "english")
    FRENCH = ("Français", "french")
    ITALIAN = ("Italiano", "italian")
    PORTUGUESE = ("Português", "portuguese")
    ROMANIAN = ("Română", "romanian")
    SPANISH = ("Español", "spanish")

    def __init__(self, display_name, filename_key):
        self.display_name = display_name
        self.filename_key = filename_key
