# Camera Capture Flow - Complete Guide

## Overview

The camera capture flow has been refactored to use the new **ContourEditorData** model, ensuring all data flows through a single, centralized handler instead of being scattered across multiple files.

## New Architecture

### Before (Old Flow - DEPRECATED)
```
User clicks Capture
  └─> TopbarWidget.on_capture_image()
      └─> ContourEditorAppWidget.on_camera_capture_requested()
          └─> Builds raw dict: {"Workpiece": [contours], "Contour": [], "Fill": []}
              └─> init_contours(raw_dict)  ❌ Bypasses data model
```

### After (New Flow - CURRENT)
```
User clicks Capture
  └─> TopbarWidget.on_capture_image()
      └─> ContourEditorAppWidget.on_camera_capture_requested()
          └─> CaptureDataHandler.handle_capture_data()  ✅ Centralized
              └─> Creates ContourEditorData
                  └─> WorkpieceManager.load_editor_data()
                      └─> Properly validated and loaded
```

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  User clicks "Capture" button        │
        │  (TopbarWidget.py)                   │
        └──────────────────────────────────────┘
                              │
                              │ Emits: capture_requested signal
                              ▼
        ┌──────────────────────────────────────┐
        │  ContourEditor.py                    │
        │  Re-emits signal                     │
        └──────────────────────────────────────┘
                              │
                              │ Signal propagation
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACQUISITION                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  ContourEditorAppWidget.py           │
        │  on_camera_capture_requested()       │
        └──────────────────────────────────────┘
                              │
                              │ controller.handle(CREATE_WORKPIECE_STEP_2)
                              ▼
        ┌──────────────────────────────────────┐
        │  Backend Controller                  │
        │  Returns: {image, height, contours}  │
        └──────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                DATA TRANSFORMATION (NEW!)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  CaptureDataHandler                  │
        │  .handle_capture_data()              │
        └──────────────────────────────────────┘
                              │
                              │ 1. Normalize contours
                              │ 2. Create Segment objects
                              │ 3. Create Layer objects
                              ▼
        ┌──────────────────────────────────────┐
        │  ContourEditorData                   │
        │  (Domain-agnostic model)             │
        └──────────────────────────────────────┘
                              │
                              │ .to_legacy_format()
                              ▼
        ┌──────────────────────────────────────┐
        │  WorkpieceManager                    │
        │  .load_editor_data()                 │
        └──────────────────────────────────────┘
                              │
                              │ .init_contour()
                              ▼
        ┌──────────────────────────────────────┐
        │  BezierSegmentManager                │
        │  Segments added to editor            │
        └──────────────────────────────────────┘
```

## Key Files and Responsibilities

### 1. **CaptureDataHandler** (`services/CaptureDataHandler.py`)
**Role:** Single source of truth for capture data processing

**Responsibilities:**
- Convert raw camera contours to ContourEditorData
- Normalize contour formats
- Handle legacy format conversion
- Validate data

**Key Methods:**
```python
CaptureDataHandler.handle_capture_data(
    workpiece_manager,
    capture_data,
    close_contour=True
)
```

### 2. **ContourEditorAppWidget** (`ui/windows/mainWindow/appWidgets/ContourEditorAppWidget.py`)
**Role:** UI-level capture coordinator

**Responsibilities:**
- Receive capture button signal
- Call backend for capture data
- Handle image updates
- Delegate to CaptureDataHandler

**Updated Method:**
```python
def on_camera_capture_requested(self):
    # Get data from backend
    result, message, data = self.controller.handle(CREATE_WORKPIECE_STEP_2)

    # Update image
    if data.get("image"):
        self.set_image(data["image"])

    # Use CaptureDataHandler (NEW!)
    editor_data = CaptureDataHandler.handle_capture_data(
        workpiece_manager=self.content_widget.contourEditor.workpiece_manager,
        capture_data=data,
        close_contour=True
    )
```

### 3. **MainApplicationFrame** (`contour_editor/ContourEditor.py`)
**Role:** Provide high-level API

**New Method:**
```python
def load_capture_data(self, capture_data, close_contour=True):
    """
    Preferred method for loading capture data.
    Uses CaptureDataHandler internally.
    """
    from pl_ui.contour_editor.services.CaptureDataHandler import CaptureDataHandler

    return CaptureDataHandler.handle_capture_data(
        workpiece_manager=self.contourEditor.workpiece_manager,
        capture_data=capture_data,
        close_contour=close_contour
    )
```

### 4. **WorkpieceManager** (`managers/workpiece_manager.py`)
**Role:** Editor data manager

**Key Method:**
```python
def load_editor_data(self, editor_data: ContourEditorData, close_contour=True):
    """Load domain-agnostic ContourEditorData into editor"""
    contours_by_layer = editor_data.to_legacy_format()
    self.init_contour(contours_by_layer, close_contour=close_contour)
    self.current_workpiece = None  # Clear workpiece reference
    return editor_data
```

## Data Formats

### Input (from backend):
```python
capture_data = {
    "image": np.ndarray,           # Camera image
    "height": float,               # Measured height
    "contours": np.ndarray         # Detected contours (N, 1, 2) or (N, 2)
}
```

### Intermediate (ContourEditorData):
```python
editor_data = ContourEditorData()
editor_data.layers = {
    "Workpiece": Layer(
        name="Workpiece",
        segments=[
            Segment(
                points=[QPointF(x1, y1), QPointF(x2, y2), ...],
                controls=[...],
                settings={}
            )
        ]
    ),
    "Contour": Layer(...),  # Empty initially
    "Fill": Layer(...)      # Empty initially
}
```

### Legacy Format (for BezierSegmentManager):
```python
contours_by_layer = {
    "Workpiece": {
        "contours": [np.array([[x, y], ...]).reshape(-1, 1, 2)],
        "settings": [{}]
    },
    "Contour": {"contours": [], "settings": []},
    "Fill": {"contours": [], "settings": []}
}
```

## Benefits of New Flow

### ✅ **Centralized**
All capture logic in **one place** (`CaptureDataHandler`)

### ✅ **Type-Safe**
Uses structured `ContourEditorData` instead of raw dicts

### ✅ **Validated**
Automatic validation via `ContourEditorData.validate()`

### ✅ **Consistent**
Same data flow as workpiece loading

### ✅ **Maintainable**
Clear separation of concerns

### ✅ **Testable**
Can test CaptureDataHandler independently

## Migration Guide

### Old Code (DEPRECATED):
```python
# DON'T DO THIS
contours_by_layer = {
    "Workpiece": [contours],
    "Contour": [],
    "Fill": []
}
self.init_contours(contours_by_layer)
```

### New Code (PREFERRED):
```python
# Option 1: Via CaptureDataHandler (most control)
from pl_ui.contour_editor.services.CaptureDataHandler import CaptureDataHandler

editor_data = CaptureDataHandler.handle_capture_data(
    workpiece_manager=manager,
    capture_data=data,
    close_contour=True
)

# Option 2: Via MainApplicationFrame (convenience)
editor_data = main_frame.load_capture_data(capture_data)
```

## Testing the New Flow

### Manual Test:
1. Click "Capture" button in the UI
2. Check console for new output:
   ```
   ✅ CaptureDataHandler: Loaded capture data into editor
      - Layers: ['Workpiece', 'Contour', 'Fill']
      - Statistics: {...}

   === Capture Data Summary ===
   Workpiece: 1 segments, 150 points
   Contour: 0 segments, 0 points
   Fill: 0 segments, 0 points
   ============================
   ```

### Programmatic Test:
```python
# Create test capture data
test_data = {
    "contours": np.array([
        [[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]
    ], dtype=np.float32),
    "height": 50.0
}

# Load via CaptureDataHandler
editor_data = CaptureDataHandler.handle_capture_data(
    workpiece_manager=manager,
    capture_data=test_data
)

# Verify
assert editor_data is not None
assert "Workpiece" in editor_data.get_layer_names()
assert editor_data.get_layer("Workpiece").segments[0].points is not None
```

## Troubleshooting

### Issue: No contours appearing after capture

**Check:**
1. Backend returns valid contours in capture_data
2. CaptureDataHandler prints summary
3. Console shows "✅ CaptureDataHandler: Loaded..."

**Fix:**
```python
# Add debug logging
print("Capture data:", capture_data)
print("Contours shape:", capture_data.get("contours").shape if capture_data.get("contours") is not None else None)
```

### Issue: Wrong contour format

**Check:**
- ContourEditorData._normalize_contour() warnings
- Expected format: (N, 1, 2)

**Fix:**
The handler automatically normalizes, but verify input is 2D coordinates.

## Future Enhancements

- [ ] Add support for multiple contour layers from capture
- [ ] Implement contour validation rules
- [ ] Add capture metadata (timestamp, camera settings)
- [ ] Support for capture presets
- [ ] Batch capture support

## Summary

The refactored capture flow:
1. **Centralizes** all capture logic in `CaptureDataHandler`
2. **Uses** the domain-agnostic `ContourEditorData` model
3. **Validates** data automatically
4. **Maintains** backward compatibility via legacy format
5. **Simplifies** future maintenance and testing

All capture operations now flow through a **single, well-defined path** instead of being scattered across multiple files!