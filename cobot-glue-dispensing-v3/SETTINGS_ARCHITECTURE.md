# Settings Architecture Documentation

## Overview

This document describes the standardized settings persistence architecture implemented to ensure consistent handling of all settings types while maintaining application isolation.

## Architecture Principles

### 1. Application-Specific Storage Isolation
- Each application has its own isolated storage under `src/applications/{app_name}/storage/`
- No shared settings files between applications
- Clean separation of concerns

### 2. Two Types of Settings

#### Core Settings
**Definition**: Settings required by ALL applications, handled by base controllers/services

**Files**:
- `camera_settings.json` - Camera configuration for vision system
- `robot_config.json` - Robot configuration and calibration data

**Characteristics**:
- Must exist in every application's storage
- Accessed by base services (VisionService, RobotService, etc.)
- Shared functionality across all applications

#### Application-Specific Settings
**Definition**: Settings unique to a specific application, registered by the application when loaded

**Examples**:
- `glue_settings.json` - Glue dispensing parameters (only for glue_dispensing_application)
- `glue_cell_config.json` - Glue cell configuration (only for glue_dispensing_application)
- `spray_settings.json` - Spray parameters (only for spray applications)

**Characteristics**:
- Only exist in their respective application's storage
- Registered via ApplicationSettingsRegistry when application loads
- Application-specific validation and handling

## Directory Structure

```
src/
├── applications/
│   ├── glue_dispensing_application/
│   │   ├── storage/
│   │   │   ├── settings/
│   │   │   │   ├── camera_settings.json      # Core setting (copy)
│   │   │   │   ├── robot_config.json         # Core setting (copy)
│   │   │   │   ├── glue_settings.json        # App-specific setting
│   │   │   │   └── glue_cell_config.json     # App-specific setting
│   │   │   ├── data/
│   │   │   ├── templates/
│   │   │   ├── cache/
│   │   │   └── logs/
│   │   └── ...
│   └── other_application/
│       ├── storage/
│       │   ├── settings/
│       │   │   ├── camera_settings.json      # Core setting (copy)
│       │   │   ├── robot_config.json         # Core setting (copy)
│       │   │   └── other_app_settings.json   # App-specific setting
│       │   └── ...
│       └── ...
└── backend/
    └── system/
        └── storage/
            └── settings/                     # Legacy location (deprecated)
```

## Key Components

### 1. ApplicationContext
**Location**: `src/core/application/ApplicationContext.py`

**Purpose**: Provides global context for the current running application, allowing base services to access core settings from the correct application storage.

**Key Functions**:
- `set_current_application(app_name)` - Set which application is currently running
- `get_core_settings_path(filename)` - Get path to core settings in current app storage
- `is_application_context_set()` - Check if application context is set

### 2. ApplicationStorageResolver
**Location**: `src/backend/system/utils/ApplicationStorageResolver.py`

**Purpose**: Provides path resolution for application-specific storage locations.

**Key Methods**:
- `get_settings_path(app_name, settings_type)` - Get settings file path
- `get_app_root_path(app_name)` - Get application root directory
- `create_application_structure(app_name)` - Create full directory structure

### 3. BaseApplicationSettingsHandler
**Location**: `src/backend/system/settings/BaseApplicationSettingsHandler.py`

**Purpose**: Standardized base class for all settings handlers with consistent validation and error handling.

**Features**:
- Transaction-like save operations with rollback
- Consistent validation framework
- Standardized error handling
- Default settings creation

## Implementation Flow

### Application Startup
1. Application sets context: `set_current_application("glue_dispensing_application")`
2. Base services use ApplicationContext to find core settings
3. Application registers its specific settings via ApplicationSettingsRegistry
4. All settings handlers use application-specific storage paths

### Settings Access
1. **Core Settings**: Base services use ApplicationContext to get paths
2. **App Settings**: Handlers use ApplicationStorageResolver directly
3. **Fallback**: Graceful degradation to legacy paths if context not set

### Settings Persistence
1. All handlers extend BaseApplicationSettingsHandler
2. Validation occurs before save operations
3. Transaction-like saves with rollback capability
4. Default settings created automatically if missing

## Migration Strategy

### Core Settings Migration
- Copy `camera_settings.json` and `robot_config.json` to each application's storage
- Update base services to use ApplicationContext for path resolution
- Maintain backward compatibility with fallback paths

### Application-Specific Settings Migration
- Move application-specific settings to respective application storage
- Update handlers to use ApplicationStorageResolver
- Preserve existing functionality and data

## Benefits

### 1. Isolation
- Applications cannot interfere with each other's settings
- Clean separation reduces debugging complexity
- Easy to backup/restore individual application configurations

### 2. Consistency
- Standardized handling across all settings types
- Consistent validation and error handling
- Uniform transaction-like save operations

### 3. Maintainability
- Clear distinction between core and application-specific settings
- Modular architecture supports easy addition of new applications
- Centralized path resolution logic

### 4. Reliability
- Transaction-like saves prevent data corruption
- Automatic backup creation during migrations
- Graceful fallback mechanisms

## Usage Examples

### Setting Application Context (in main.py)
```python
from core.application.ApplicationContext import set_current_application

# Set the application context early in startup
set_current_application("glue_dispensing_application")
```

### Accessing Core Settings (in base services)
```python
from core.application.ApplicationContext import get_core_settings_path

# VisionService accessing camera settings
config_path = get_core_settings_path("camera_settings.json")
if config_path is None:
    # Fallback to legacy path
    config_path = "legacy/path/camera_settings.json"
```

### Application-Specific Settings Handler
```python
from backend.system.settings.BaseApplicationSettingsHandler import BaseApplicationSettingsHandler
from backend.system.utils.ApplicationStorageResolver import get_app_settings_path

class CustomSettingsHandler(BaseApplicationSettingsHandler):
    def __init__(self):
        settings_file = get_app_settings_path("my_app", "custom_settings")
        super().__init__(settings_file)
```

## Best Practices

### 1. Core Settings
- Keep core settings minimal (only truly universal settings)
- Ensure core settings are copied to all applications
- Use ApplicationContext in base services

### 2. Application-Specific Settings
- Register settings via ApplicationSettingsRegistry
- Use descriptive settings type names
- Implement proper validation in handlers

### 3. Path Resolution
- Always use ApplicationStorageResolver or ApplicationContext
- Never hardcode storage paths
- Implement fallback mechanisms for compatibility

### 4. Error Handling
- Use BaseApplicationSettingsHandler for consistency
- Implement proper validation before saves
- Provide meaningful error messages

## Future Considerations

### 1. Multi-Application Support
- Architecture supports multiple applications running simultaneously
- ApplicationContext can be extended for multi-app scenarios
- Settings isolation prevents conflicts

### 2. Settings Versioning
- BaseApplicationSettingsHandler can be extended for version migration
- Clear upgrade paths for settings schema changes
- Backward compatibility maintenance

### 3. Configuration Management
- Centralized configuration for deployment scenarios
- Environment-specific settings override mechanisms
- Configuration validation at startup