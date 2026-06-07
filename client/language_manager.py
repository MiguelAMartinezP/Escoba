import json
import os
from kivy.properties import StringProperty
from kivy.event import EventDispatcher


class LanguageManager(EventDispatcher):
    """Manages language translations for the application."""

    __events__ = ('on_language_changed',)

    def __init__(self):
        super().__init__()
        self.languages = {}
        self.current_language = "es"
        self.languages_dir = os.path.join(os.path.dirname(__file__), "languages")
        self.load_languages()

    def on_language_changed(self, *args):
        """Event fired when the active language changes."""
        pass
    
    def load_languages(self):
        """Load all available language files from the languages directory."""
        if not os.path.exists(self.languages_dir):
            print(f"Warning: Languages directory not found at {self.languages_dir}")
            return
        
        for filename in os.listdir(self.languages_dir):
            if filename.endswith(".json"):
                lang_code = filename.replace(".json", "")
                filepath = os.path.join(self.languages_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                    print(f"Loaded language: {lang_code}")
                except Exception as e:
                    print(f"Error loading language {lang_code}: {e}")
    
    def get_available_languages(self):
        """Return list of available language codes."""
        return list(self.languages.keys())
    
    def set_language(self, language_code):
        """Set the current language."""
        if language_code in self.languages:
            self.current_language = language_code
            self.dispatch("on_language_changed")
            print(f"Language changed to: {language_code}")
        else:
            print(f"Language {language_code} not available")
    
    def translate(self, key_path, default=""):
        """
        Get a translation string.
        
        Args:
            key_path: Dot-separated path (e.g., "menu.play")
            default: Default value if key is not found
        
        Returns:
            Translated string or default value
        """
        keys = key_path.split(".")
        current = self.languages.get(self.current_language, {})
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
        
        return current if current else default
    
    def __getitem__(self, key_path):
        """Allow dictionary-like access to translations."""
        return self.translate(key_path)


# Global instance
_language_manager = None


def get_language_manager():
    """Get or create the global language manager instance."""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager
