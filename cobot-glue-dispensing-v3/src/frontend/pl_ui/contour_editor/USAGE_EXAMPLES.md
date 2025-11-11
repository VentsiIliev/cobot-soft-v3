# Contour Editor Data Model - Usage Examples

## Overview

The contour editor now has a clean, domain-agnostic data model that separates concerns:

- **ContourEditorData**: Domain-agnostic data structure (knows nothing about workpieces)
- **WorkpieceAdapter**: Converts between Workpiece objects and ContourEditorData
- **WorkpieceManager**: Provides high-level API for both workpiece and editor data

## Architecture

```
┌─────────────────────┐
│  Workpiece Object   │ (Domain-specific)
└──────────┬──────────┘
           │
           │ WorkpieceAdapter.from_workpiece()
           ▼
┌─────────────────────┐
│ ContourEditorData   │ (Domain-agnostic)
└──────────┬──────────┘
           │
           │ to_legacy_format()
           ▼
┌─────────────────────┐
│  Contour Editor     │
└─────────────────────┘
```

## Usage Examples

### Example 1: Loading a Workpiece (Existing Workflow)

```python
from pl_ui.contour_editor.managers.workpiece_manager import WorkpieceManager

# Assuming you have a WorkpieceManager instance and a Workpiece object
workpiece_manager = WorkpieceManager(editor)

# Load workpiece (uses WorkpieceAdapter internally)
workpiece_manager.load_workpiece(my_workpiece)
```

### Example 2: Creating ContourEditorData from Scratch

```python
import numpy as np
from pl_ui.contour_editor.EditorDataModel import ContourEditorData
from shared.shared.contour_editor.BezierSegmentManager import Layer, Segment

# Create a new ContourEditorData instance
editor_data = ContourEditorData()

# Create a layer
external_layer = Layer(name="External", locked=False, visible=True)

# Create a segment with some points
segment = Segment(layer=external_layer, settings={"speed": 100})
from PyQt6.QtCore import QPointF

segment.add_point(QPointF(0, 0))
segment.add_point(QPointF(100, 0))
segment.add_point(QPointF(100, 100))
segment.add_point(QPointF(0, 100))

# Add segment to layer
external_layer.add_segment(segment)

# Add layer to editor data
editor_data.add_layer(external_layer)

# Load into editor
workpiece_manager.load_editor_data(editor_data)
```

### Example 3: Import/Export to JSON

```python
# Export to dictionary (can be serialized to JSON)
data_dict = editor_data.to_dict()

# Save to JSON file
import json
with open("contour_data.json", "w") as f:
    json.dump(data_dict, f, indent=2)

# Load from JSON file
with open("contour_data.json", "r") as f:
    loaded_dict = json.load(f)

# Create ContourEditorData from dictionary
editor_data = ContourEditorData.from_dict(loaded_dict)
```

### Example 4: Working with Legacy Format

```python
# Create from legacy format
legacy_data = {
    "Workpiece": {
        "contours": [np.array([[0, 0], [100, 0], [100, 100]], dtype=np.float32).reshape(-1, 1, 2)],
        "settings": [{"speed": 50}]
    },
    "Contour": {
        "contours": [np.array([[10, 10], [90, 10]], dtype=np.float32).reshape(-1, 1, 2)],
        "settings": [{"spray_width": 5}]
    }
}

editor_data = ContourEditorData.from_legacy_format(legacy_data)

# Convert back to legacy format
legacy_format = editor_data.to_legacy_format()
```

### Example 5: Exporting from Editor

```python
# Export current editor state as ContourEditorData
editor_data = workpiece_manager.export_editor_data()

# Get statistics
stats = editor_data.get_statistics()
print(f"Total layers: {stats['total_layers']}")
print(f"Total segments: {stats['total_segments']}")
print(f"Total points: {stats['total_points']}")

# Validate the data
is_valid, errors = editor_data.validate()
if not is_valid:
    print("Validation errors:", errors)
```

### Example 6: Converting Back to Workpiece Format

```python
# Export editor data in workpiece-compatible format
workpiece_data = workpiece_manager.export_to_workpiece_data()

# workpiece_data contains:
# {
#     "main_contour": np.ndarray,      # Main workpiece boundary
#     "main_settings": dict,            # Settings for main contour
#     "spray_pattern": {
#         "Contour": [                  # List of spray contours
#             {"contour": np.ndarray, "settings": dict},
#             ...
#         ],
#         "Fill": [                     # List of fill patterns
#             {"contour": np.ndarray, "settings": dict},
#             ...
#         ]
#     }
# }

# Use this data to create or update a Workpiece object
# (This requires other workpiece-specific fields)
```

### Example 7: Using WorkpieceAdapter Directly

```python
from pl_ui.contour_editor.adapters.WorkpieceAdapter import WorkpieceAdapter

# Convert Workpiece to ContourEditorData
editor_data = WorkpieceAdapter.from_workpiece(my_workpiece)

# Print summary
WorkpieceAdapter.print_summary(editor_data)

# Convert ContourEditorData back to workpiece format
workpiece_data = WorkpieceAdapter.to_workpiece_data(editor_data)
```

## Key Benefits

1. **Separation of Concerns**: The editor doesn't need to know about workpieces
2. **Testability**: Easy to create test data without domain objects
3. **Flexibility**: Can use the editor for non-workpiece data
4. **Serialization**: Built-in JSON support for saving/loading
5. **Validation**: Automatic data validation
6. **Statistics**: Built-in statistics and reporting

## API Reference

### ContourEditorData

**Methods:**
- `add_layer(layer)` - Add or replace a layer
- `get_layer(name)` - Get layer by name
- `remove_layer(name)` - Remove a layer
- `get_layer_names()` - Get all layer names
- `get_all_segments()` - Get all segments from all layers
- `clear()` - Clear all data
- `to_dict()` - Export to dictionary
- `from_dict(data)` - Create from dictionary (classmethod)
- `to_legacy_format()` - Export to legacy format
- `from_legacy_format(data)` - Create from legacy format (classmethod)
- `get_statistics()` - Get data statistics
- `validate()` - Validate data consistency

### WorkpieceAdapter

**Methods:**
- `from_workpiece(workpiece)` - Convert Workpiece to ContourEditorData (classmethod)
- `to_workpiece_data(editor_data)` - Convert to workpiece format (classmethod)
- `print_summary(editor_data)` - Print summary (classmethod)

### WorkpieceManager

**Workpiece Methods:**
- `load_workpiece(workpiece)` - Load a Workpiece object
- `get_current_workpiece()` - Get current workpiece
- `set_current_workpiece(workpiece)` - Set current workpiece
- `export_to_workpiece_data()` - Export to workpiece format

**Editor Data Methods:**
- `load_editor_data(editor_data)` - Load ContourEditorData
- `export_editor_data()` - Export as ContourEditorData
- `get_contours()` - Get raw contours data
- `clear_workpiece()` - Clear all data

**Validation & Stats:**
- `get_workpiece_statistics()` - Get statistics
- `validate_workpiece_data()` - Validate data

## Migration Guide

### Before (Old Code)

```python
# Old way - tightly coupled to workpiece
from pl_ui.contour_editor.services.workpiece_loader import load_workpiece, init_workpiece

workpiece, contours = load_workpiece(my_workpiece)
contours_normalized = init_workpiece(contours)
manager.init_contour(contours_normalized)
```

### After (New Code)

```python
# New way - using WorkpieceAdapter
from pl_ui.contour_editor.managers.workpiece_manager import WorkpieceManager

manager = WorkpieceManager(editor)
manager.load_workpiece(my_workpiece)  # Everything handled internally
```

Or for domain-agnostic usage:

```python
# Working without workpieces
from pl_ui.contour_editor.EditorDataModel import ContourEditorData

editor_data = ContourEditorData.from_legacy_format(my_data)
manager.load_editor_data(editor_data)
```