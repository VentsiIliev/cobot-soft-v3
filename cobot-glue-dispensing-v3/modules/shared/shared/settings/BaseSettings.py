class Settings:
    def __init__(self,):
        self._settings = {}

    def set_value(self, key, value):
        """Generic method to set a setting value by key."""
        self._settings[key] = value

    def get_value(self, key, default=None):
        """Generic method to get a setting value by key. Returns default if key not found."""
        return self._settings.get(key, default)

    def remove_value(self, key):
        """Remove a specific setting by key."""
        if key in self._settings:
            del self._settings[key]

    def get_all_settings(self):
        """Returns all the settings as a dictionary."""
        return self._settings

    def clear_all_settings(self):
        """Clears all settings."""
        self._settings.clear()

    def save_settings(self, filepath):
        """Save the settings to a file."""
        with open(filepath, 'w') as f:
            for key, value in self._settings.items():
                f.write(f"{key}={value}\n")

    def load_settings(self, filepath):
        """Load settings from a file."""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    key, value = line.strip().split('=', 1)
                    self._settings[key] = value
        except FileNotFoundError:
            print(f"Settings file {filepath} not found.")

    def toDict(self):
        return self._settings

