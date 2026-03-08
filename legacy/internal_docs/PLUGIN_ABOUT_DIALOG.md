# Plugin About Dialog Feature

## Overview

When a plugin has a description available, users can now click the **"About"** text in the step block to see full plugin information in a dedicated dialog. This feature works for all plugin types: filters, contact point detectors, force models, and elastic models.

## UI Usage

1. **Look for the "About" link** in the title bar of any step block (appears as underlined text)
2. **Click "About"** to open a dialog with complete plugin information
3. The dialog shows:
   - Plugin name
   - Step type and ID
   - Full description
   - Version (if available)
   - Mathematical equation (if available)
   - DOI link (if available)

## Features

✅ Click-to-expand functionality (no more tooltip limitations)  
✅ Works for all plugin types with descriptions  
✅ Formatted dialog with readable layout  
✅ DOI links are clickable (opens in browser)  
✅ Only shows "About" when description is available  

## Implementation Details

**Files Modified:**

1. **softmech/ui/designer/widgets/block_pipeline_editor.py**
   - Updated `StepBlockWidget.__init__()` to show About for all types
   - Added `_show_about_dialog()` method to display plugin information
   - About label is now clickable (mouse press event)
   - Dialog includes all available plugin metadata

### What Changed

**Before:** About was only shown for filter and contact_point plugins, displayed as a tooltip

**After:** About is shown for ALL plugin types (filters, contact_point, force_model, elastic_model) and displays as a full dialog when clicked

### Dialog Contents

```
┌─────────────────────────────────┐
│ Plugin Name                     │
│ Type: force_model | ID: hertz   │
├─────────────────────────────────┤
│ Full description text...        │
│                                 │
│ Version: 1.1.0                 │
│ Equation: F(δ) = ...           │
│ DOI: http://doi.org/...        │
└─────────────────────────────────┘
```

---

## For Plugin Developers

To ensure your plugin shows a nice About dialog:

```python
# In your plugin module (__init__.py)

NAME = "My Force Model"
DESCRIPTION = "Detailed description of what the model does, assumptions, and use cases."
VERSION = "1.0.0"
EQUATION = r"F(\delta) = model_equation"
DOI = "10.1234/journal.2024.xxxxx"  # or full URL
```

All of these fields are optional. The About dialog will only show sections for which you've provided content.
