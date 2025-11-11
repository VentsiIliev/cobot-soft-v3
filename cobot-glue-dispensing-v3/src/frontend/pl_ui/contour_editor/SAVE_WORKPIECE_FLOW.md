# Save Workpiece Flow - Complete Analysis

## Executive Summary

The save workpiece flow is **scattered across 8+ files** and **does NOT use the new ContourEditorData model**. It extracts data directly from BezierSegmentManager using the legacy `to_wp_data()` method and bypasses the structured data model entirely.

## Current Flow (AS-IS)

### Phase 1: Button Click → Form Display

```
User clicks "Save" button (First Click)
  ↓
TopbarWidget.save_button → emits save_requested signal
  ↓
MainApplicationFrame.on_first_save_clicked() (line 418)
  ↓
- Creates CreateWorkpieceForm
- Shows form in sliding panel
- Reconnects save button to on_workpiece_save_clicked()
```

### Phase 2: Form Submit → Data Extraction

```
User fills form and clicks "Save" again (Second Click)
  ↓
MainApplicationFrame.on_workpiece_save_clicked() (line 521)
  ↓
CreateWorkpieceForm.onSubmit() (line 548)
  ↓
- Collects form data (name, description, tool, gripper, etc.)
- Validates mandatory fields
- Emits data_submitted signal with form data
```

### Phase 3: Data Aggregation

```
CreateWorkpieceForm.data_submitted signal
  ↓
Connected to: save_workpiece_requested.emit(data) (line 425)
  ↓
MainApplicationFrame.save_workpiece_requested signal emitted
  ↓
Connected to: via_camera_on_create_workpiece_submit(data) (line 26 in ContourEditorAppWidget)
  ↓
ContourEditorAppWidget.via_camera_on_create_workpiece_submit() (line 99)
  ↓
Calls: manager.to_wp_data() ❌ BYPASSES ContourEditorData!
  ↓
Extracts raw segments:
  - wp_contours_data['Workpiece'] → Main contour
  - wp_contours_data['Contour'] → Spray pattern contours
  - wp_contours_data['Fill'] → Fill patterns
  ↓
Merges form data + contour data
  ↓
Calls: controller.handle(SAVE_WORKPIECE, data)
```

### Phase 4: Controller → Service

```
Controller.handle(SAVE_WORKPIECE, data)
  ↓
Controller.saveWorkpiece(data) (line 208)
  ↓
Sends request: Constants.WORKPIECE_SAVE ("workpiece/save")
  ↓
requestSender.sendRequest(request, data)
  ↓
[Backend processes request - likely in MessageBroker]
  ↓
WorkpieceService.saveWorkpiece(workpiece) (line 33)
```

### Phase 5: Repository → Disk

```
WorkpieceService.saveWorkpiece(workpiece)
  ↓
WorkpieceJsonRepository.saveWorkpiece(workpiece) (line 155)
  ↓
Checks if workpiece exists by ID:
  - If exists: Overwrites existing JSON file
  - If new: Creates timestamped folder structure
    └─ workpieces/YYYY-MM-DD/YYYY-MM-DD_HH-MM-SS-fff/timestamp_workpiece.json
  ↓
Serializes workpiece using Workpiece.serialize()
  ↓
Writes JSON to file
  ↓
Updates in-memory data list
  ↓
Returns: (True, "Workpiece saved successfully")
```

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  User clicks "Save" button #1        │
        │  (TopbarWidget.save_button)          │
        └──────────────────────────────────────┘
                              │
                              │ emits: save_requested
                              ▼
        ┌──────────────────────────────────────┐
        │  MainApplicationFrame                │
        │  .on_first_save_clicked()            │
        └──────────────────────────────────────┘
                              │
                              │ 1. Shows CreateWorkpieceForm
                              │ 2. Reconnects button to on_workpiece_save_clicked
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FORM DISPLAY                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  User fills form                     │
        │  User clicks "Save" button #2        │
        └──────────────────────────────────────┘
                              │
                              │ emits: save_requested (2nd time)
                              ▼
        ┌──────────────────────────────────────┐
        │  MainApplicationFrame                │
        │  .on_workpiece_save_clicked()        │
        └──────────────────────────────────────┘
                              │
                              │ calls: createWorkpieceForm.onSubmit()
                              ▼
        ┌──────────────────────────────────────┐
        │  CreateWorkpieceForm                 │
        │  .onSubmit()                         │
        └──────────────────────────────────────┘
                              │
                              │ 1. Validates form
                              │ 2. Collects data
                              │ 3. emits: data_submitted(data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATA EXTRACTION (LEGACY!)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  data_submitted signal received      │
        │  → save_workpiece_requested.emit()   │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  ContourEditorAppWidget              │
        │  .via_camera_on_create_workpiece     │
        │   _submit()                          │
        └──────────────────────────────────────┘
                              │
                              │ ❌ PROBLEM: Uses legacy method!
                              ▼
        ┌──────────────────────────────────────┐
        │  manager.to_wp_data()                │
        │  (BezierSegmentManager method)       │
        └──────────────────────────────────────┘
                              │
                              │ Extracts raw segments by layer
                              ▼
        ┌──────────────────────────────────────┐
        │  wp_contours_data = {                │
        │    "Workpiece": [...],               │
        │    "Contour": [...],                 │
        │    "Fill": [...]                     │
        │  }                                   │
        └──────────────────────────────────────┘
                              │
                              │ Merge with form data
                              ▼
        ┌──────────────────────────────────────┐
        │  Complete workpiece data dict        │
        │  - Form fields (name, desc, etc.)    │
        │  - Contour data                      │
        │  - Spray patterns                    │
        └──────────────────────────────────────┘
                              │
                              │ controller.handle(SAVE_WORKPIECE, data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CONTROLLER LAYER                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  Controller.saveWorkpiece(data)      │
        └──────────────────────────────────────┘
                              │
                              │ sendRequest("workpiece/save", data)
                              ▼
        ┌──────────────────────────────────────┐
        │  RequestSender                       │
        │  (IPC/Message passing)               │
        └──────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND SERVICE                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │  WorkpieceService                    │
        │  .saveWorkpiece(workpiece)           │
        └──────────────────────────────────────┘
                              │
                              │ repository.saveWorkpiece()
                              ▼
        ┌──────────────────────────────────────┐
        │  WorkpieceJsonRepository             │
        │  .saveWorkpiece(workpiece)           │
        └──────────────────────────────────────┘
                              │
                              │ 1. Serialize workpiece
                              │ 2. Check if exists by ID
                              ▼
        ┌──────────────────────────────────────┐
        │  Exists?                             │
        └──────────────────────────────────────┘
                    │                    │
              YES   │                    │ NO
                    ▼                    ▼
        ┌──────────────────┐  ┌──────────────────────┐
        │ Overwrite file   │  │ Create new timestamped│
        │ Update in-memory │  │ folder & file        │
        └──────────────────┘  └──────────────────────┘
                    │                    │
                    └──────────┬─────────┘
                               ▼
        ┌──────────────────────────────────────┐
        │  JSON file written to disk:          │
        │  workpieces/                         │
        │    YYYY-MM-DD/                       │
        │      YYYY-MM-DD_HH-MM-SS-fff/        │
        │        timestamp_workpiece.json      │
        └──────────────────────────────────────┘
```

## Files Involved (8 Files)

| # | File | Lines | Role |
|---|------|-------|------|
| 1 | `TopbarWidget.py` | 131 | Save button definition |
| 2 | `ContourEditor.py` (MainApplicationFrame) | 418-569 | Button click handlers, form display |
| 3 | `CreateWorkpieceForm.py` | 548-614 | Form validation & data collection |
| 4 | `ContourEditorAppWidget.py` | 99-114 | Data extraction & aggregation |
| 5 | `BezierSegmentManager.py` | 219-283 | Legacy to_wp_data() method |
| 6 | `Controller.py` | 208-216 | Request routing |
| 7 | `WorkpieceService.py` | 33-44 | Business logic |
| 8 | `WorkpieceJsonRepository.py` | 155-230 | File persistence |

## Data Transformations

### Step 1: Form Data (from CreateWorkpieceForm)
```python
{
    "workpieceId": "WP123",
    "name": "My Workpiece",
    "description": "Description",
    "toolId": "0",
    "gripperId": "0",
    "glueType": "Type A",
    "program": "Trace",
    "material": "Material1",
    "offset": "0",
    "height": "50",
    "glue_qty": "100",
    "spray_width": "10",
    "pickup_point": "100.5,200.3"
}
```

### Step 2: Contour Data (from manager.to_wp_data())
```python
{
    "Workpiece": [
        {
            "contour": np.array([[[x,y]], ...], dtype=float32),
            "settings": {}
        }
    ],
    "Contour": [
        {
            "contour": np.array([[[x,y]], ...], dtype=float32),
            "settings": {"speed": 100, "spray_width": 5}
        },
        ...
    ],
    "Fill": [
        {
            "contour": np.array([[[x,y]], ...], dtype=float32),
            "settings": {}
        }
    ]
}
```

### Step 3: Merged Data (sent to backend)
```python
{
    # Form fields
    "workpieceId": "WP123",
    "name": "My Workpiece",
    "description": "Description",
    ...

    # Extracted from editor
    "contour": wp_contours_data["Workpiece"][0],  # Main contour
    "sprayPattern": {
        "Contour": wp_contours_data["Contour"],
        "Fill": wp_contours_data["Fill"]
    },
    "contourArea": "0"
}
```

## ❌ Problems with Current Flow

### 1. **Scattered Logic**
- Save logic spread across **8 different files**
- Hard to trace, debug, or modify
- No single source of truth

### 2. **Bypasses New Data Model**
- Uses `manager.to_wp_data()` directly ❌
- Does NOT use `ContourEditorData` ❌
- Does NOT use `WorkpieceAdapter` ❌
- Inconsistent with capture flow

### 3. **Two-Stage Save Process**
- First click: Shows form
- Second click: Actually saves
- Confusing UX, complex state management

### 4. **Direct BezierSegmentManager Access**
```python
# CURRENT (BAD)
wp_contours_data = self.content_widget.contourEditor.manager.to_wp_data()
```

Should use:
```python
# SHOULD BE
editor_data = manager.export_editor_data()
workpiece_data = WorkpieceAdapter.to_workpiece_data(editor_data)
```

### 5. **Duplicate Code**
Same data extraction logic appears in:
- `ContourEditorAppWidget.via_camera_on_create_workpiece_submit()` (line 99)
- `MainApplicationFrame.on_save_workpiece_requested()` (line 89)
- `MainApplicationFrame.onStart()` (line 469)

## 🎯 Recommended Refactoring

### Create SaveWorkpieceHandler (similar to CaptureDataHandler)

```python
class SaveWorkpieceHandler:
    """Centralized handler for saving workpieces"""

    @classmethod
    def save_workpiece(cls, workpiece_manager, form_data, controller):
        """
        Single entry point for all save operations.

        1. Export editor data as ContourEditorData
        2. Use WorkpieceAdapter to convert to workpiece format
        3. Merge with form data
        4. Save via controller
        """
        # Export using new data model
        editor_data = workpiece_manager.export_editor_data()

        # Convert to workpiece format
        workpiece_data = WorkpieceAdapter.to_workpiece_data(editor_data)

        # Merge with form data
        complete_data = {**form_data, **workpiece_data}

        # Save
        return controller.handle(SAVE_WORKPIECE, complete_data)
```

### Benefits:
1. ✅ **Centralized** - One place for all save logic
2. ✅ **Consistent** - Uses same data model as capture flow
3. ✅ **Testable** - Easy to unit test
4. ✅ **Maintainable** - Clear separation of concerns
5. ✅ **Type-safe** - Uses ContourEditorData instead of raw dicts

## Key Findings

### ✅ What Works:
- Repository pattern with JSON storage
- Timestamped folder structure
- Update vs create detection by ID
- In-memory data caching

### ❌ What Doesn't Work:
- **NO use of ContourEditorData model**
- **Scattered save logic across 8 files**
- **Direct BezierSegmentManager access**
- **Duplicate data extraction code**
- **Inconsistent with capture flow**

## Conclusion

The save workpiece flow is **functionally working** but **architecturally inconsistent** with the new ContourEditorData model. It should be refactored to:

1. Use `WorkpieceManager.export_editor_data()` instead of `manager.to_wp_data()`
2. Use `WorkpieceAdapter.to_workpiece_data()` for conversion
3. Centralize logic in a `SaveWorkpieceHandler` class
4. Eliminate code duplication
5. Maintain consistency with the capture flow pattern

**The save flow currently bypasses all the new infrastructure you wanted to create!**