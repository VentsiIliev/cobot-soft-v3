# Localization System Migration Guide

This guide walks through migrating from the old scattered localization approach to the new centralized system.

## 🚀 Quick Start

### 1. Initialize in main.py
```python
# Add to your main application startup
from pl_ui.localization import setup_localization, Language

def main():
    app = QApplication([])
    setup_localization(Language.ENGLISH)  # One-time setup
    # ... rest of app initialization
```

### 2. Convert a Widget

```python
# OLD WAY ❌
from shared.localization.LanguageResourceLoader import LanguageResourceLoader
from shared.localization.enums.Message import Message
from shared.MessageBroker import MessageBroker


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.lang_loader = LanguageResourceLoader()
        broker = MessageBroker()
        broker.subscribe("Language", self.update_labels)
        self.setup_ui()

    def setup_ui(self):
        self.button = QPushButton(self.lang_loader.get_message(Message.LOGIN))

    def update_labels(self):
        self.lang_loader = LanguageResourceLoader()
        self.button.setText(self.lang_loader.get_message(Message.LOGIN))


# NEW WAY ✅
from pl_ui.localization import TranslatableWidget, TranslationKeys


class MyWidget(TranslatableWidget):
    def __init__(self):
        super().__init__()  # Automatic translation setup!
        self.setup_ui()

    def setup_ui(self):
        self.button = QPushButton()  # No text here

    def retranslate(self):  # Called automatically on language changes
        self.button.setText(self.tr(TranslationKeys.Auth.LOGIN))
```

## 📋 Step-by-Step Migration

### Step 1: Update Imports

```python
# Remove these imports:
from shared.localization.LanguageResourceLoader import LanguageResourceLoader
from shared.localization.enums.Message import Message
from shared.MessageBroker import MessageBroker

# Add this single import:
from pl_ui.localization import TranslatableWidget, TranslationKeys
```

### Step 2: Change Base Class
```python
# OLD
class MyWidget(QWidget):

# NEW  
class MyWidget(TranslatableWidget):
```

### Step 3: Remove Manual Setup
```python
# REMOVE these from __init__:
self.lang_loader = LanguageResourceLoader()
self.langLoader = LanguageResourceLoader()
broker = MessageBroker()
broker.subscribe("Language", self.update_something)
```

### Step 4: Move Translations to retranslate()
```python
# OLD - Set text immediately in setup_ui():
def setup_ui(self):
    self.button = QPushButton(self.lang_loader.get_message(Message.LOGIN))

# NEW - Create elements without text, set in retranslate():
def setup_ui(self):
    self.button = QPushButton()  # No text

def retranslate(self):
    self.button.setText(self.tr(TranslationKeys.Auth.LOGIN))
```

### Step 5: Replace Translation Calls
```python
# OLD patterns to replace:
self.lang_loader.get_message(Message.LOGIN)
self.langLoader.get_message(Message.PASSWORD)  
loader.get_message(Message.START)

# NEW pattern:
self.tr(TranslationKeys.Auth.LOGIN)
self.tr(TranslationKeys.Auth.PASSWORD)
self.tr(TranslationKeys.Dashboard.START)
```

### Step 6: Remove Manual Update Methods
```python
# REMOVE methods like these:
def update_labels(self):
    self.lang_loader = LanguageResourceLoader()
    self.button.setText(self.lang_loader.get_message(Message.LOGIN))

def updateLabels(self, message=None):
    # Manual translation updates

# The retranslate() method handles this automatically!
```

## 🔄 Common Patterns

### Pattern 1: Labels with Dynamic Data
```python
# OLD
def update_user_info(self):
    self.label.setText(f"{self.lang_loader.get_message(Message.USER)}: {username}")

# NEW
def retranslate(self):
    self.update_user_info()  # Call update method from retranslate

def update_user_info(self):
    username = self.get_current_username()
    self.label.setText(f"{self.tr(TranslationKeys.User.USER)}: {username}")
```

### Pattern 2: Dialog Classes
```python
# OLD
class MyDialog(QDialog):

# NEW
from pl_ui.localization import TranslatableDialog
class MyDialog(TranslatableDialog):
```

### Pattern 3: Non-Widget Classes
```python
# NEW - For services, controllers, etc.
from pl_ui.localization import TranslatableObject

class MyService(TranslatableObject):
    def get_error_message(self):
        return self.tr(TranslationKeys.Status.ERROR)
```

## 🎯 Translation Key Organization

Use the organized keys from `TranslationKeys`:

```python
# Authentication
TranslationKeys.Auth.LOGIN
TranslationKeys.Auth.PASSWORD
TranslationKeys.Auth.USER_NOT_FOUND

# User Management
TranslationKeys.User.FIRST_NAME  
TranslationKeys.User.ROLE
TranslationKeys.User.SESSION_DURATION

# Dashboard Controls
TranslationKeys.Dashboard.START
TranslationKeys.Dashboard.STOP
TranslationKeys.Dashboard.PAUSE

# Navigation
TranslationKeys.Navigation.WORK
TranslationKeys.Navigation.SERVICE
TranslationKeys.Navigation.BACK

# Or use shortcuts for common ones:
TranslationKeys.LOGIN  # Same as TranslationKeys.Auth.LOGIN
TranslationKeys.START  # Same as TranslationKeys.Dashboard.START
```

## ✅ Migration Checklist

For each widget you migrate:

- [ ] Remove `LanguageResourceLoader` import and usage
- [ ] Remove `MessageBroker` subscription for language changes  
- [ ] Change base class to `TranslatableWidget` or `TranslatableDialog`
- [ ] Move translation calls from `setup_ui()` to `retranslate()`
- [ ] Replace `get_message()` calls with `self.tr(TranslationKeys.*)`
- [ ] Remove manual translation update methods
- [ ] Test language switching still works

## 🧪 Testing

Test your migrated widgets:

```python
# Quick test in any widget
def test_translations(self):
    print(f"Current language: {self.translator.current_language}")
    print(f"Login text: {self.tr(TranslationKeys.Auth.LOGIN)}")
    
    # Test language switching
    self.translator.set_language(Language.SPANISH)
    print(f"Login in Spanish: {self.tr(TranslationKeys.Auth.LOGIN)}")
```

## 🚨 Common Issues

### Issue: "AttributeError: 'MyWidget' object has no attribute 'tr'"
**Fix**: Make sure you inherit from `TranslatableWidget` and call `super().__init__()`

### Issue: Translations not updating on language change
**Fix**: Make sure your `retranslate()` method is implemented and updates all text

### Issue: "Cannot import TranslationKeys"
**Fix**: Make sure you have `from pl_ui.localization import TranslationKeys`

### Issue: Old and new systems conflicting
**Fix**: Remove all old localization code before testing new system

## 📈 Benefits After Migration

- ✅ **90% less boilerplate code**
- ✅ **Automatic language change handling** 
- ✅ **No more manual MessageBroker subscriptions**
- ✅ **Organized translation keys**
- ✅ **Better separation of concerns**
- ✅ **Easier to test and mock**
- ✅ **Type-safe translation keys**
- ✅ **Consistent API across all widgets**

## 🎉 You're Done!

Your widget now:
- Automatically updates when language changes
- Uses clean, organized translation keys  
- Has no scattered localization imports
- Follows a consistent pattern across the app
- Is easier to maintain and test