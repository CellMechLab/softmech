# Force Model Fitting Region Selection

## Overview

Users can now select a specific indentation depth range for force model fitting. This is useful when:
- Data has artifacts at very small or very large indentations
- Only a middle portion of the curve represents reliable contact mechanics
- You want to exclude noise from shallow or deep regions

## UI Usage

When editing force model parameters in the Designer:

1. **Open the parameters dialog** by clicking "Edit" on a force model step
2. **Locate the "Fitting Region (Indentation Depth)" section**
3. **Set the range in nanometers (nm):**
   - **Minimum Indentation Depth**: Minimum indentation depth to include in fit (nm)
   - **Maximum Indentation Depth**: Maximum indentation depth to include in fit (nm)
4. **Typical range: 0-10000 nm (0-10 μm)**
5. **Leave at 0 to use full available range** (default behavior)

Example values:
- Min: `100` (0.1 μm minimum indentation)
- Max: `5000` (5 μm maximum indentation)

## Technical Details

### API for Plugin Developers

**ForceModel Base Class Parameters:**

Parameters are in **nanometers (nm)** with typical values 0-10000 nm (0-10 μm).

```python
from softmech.core.plugins import ForceModel

class MyForceModel(ForceModel):
    # Fitting region parameters (in nanometers, automatically inherited)
    min_indentation_depth: float = 0.0  # 0 = use minimum available
    max_indentation_depth: float = 0.0  # 0 = use maximum available
    
    def calculate(self, x, y, curve=None):
        # x is in meters (SI), parameters are in nm
        # _get_fitting_region() handles the unit conversion
        x_fit, y_fit = self._get_fitting_region(x, y)
        
        # Now fit with x_fit, y_fit only
        # ...
        return [result]
```

**Unit Conversion:** The helper method `_get_fitting_region()` automatically converts:
- Input x data from **meters** to **nanometers** for comparison
- Parameters are in **nanometers** 
- Returns data in original **meters**

### Implementation in Hertz Model

The Hertz model now automatically applies region filtering (in nanometers):

```python
def calculate(self, x, y, curve=None):
    # x is in meters (SI), min/max are in nm
    # ... validation ...
    
    # Apply fitting region selection (handles m → nm conversion)
    x_fit, y_fit = self._get_fitting_region(x, y)
    
    # Fit with selected region
    # ...
```

---

## Under the Hood

**File Changes:**

1. **softmech/core/plugins/base.py**
   - Added `min_indentation_depth` and `max_indentation_depth` parameters to `ForceModel` class (in nm)
   - Added `_get_fitting_region(x, y)` helper method
   - **Automatic unit conversion**: input x in meters → converted to nm for comparison → original meters returned
   - Handles 0 values as "use full available range"

2. **softmech/plugins/force_models/hertz.py**
   - Updated `calculate()` to use `_get_fitting_region()` before fitting
   - Full documentation of fitting region parameter behavior

3. **softmech/ui/designer/widgets/block_pipeline_editor.py**
   - Enhanced `ParametersDialog` to group and highlight region parameters
   - Range selector: 0-10000 nm (0-10 μm) with 0.1 nm precision
   - Suffix: " nm" for clarity
   - Tooltips with units and range information

---

## Legacy Plugin Porting

When porting force models from `protocols/fmodels/`, apply the same pattern:

```python
# In your legacy force model's fitting routine:
x_fit, y_fit = self._get_fitting_region(x, y)
# x_fit, y_fit are now in the specified fitting region
# Parameters (min/max) are in nm, input x in meters, conversion is automatic
```

The `_get_fitting_region()` method handles:
- Converting 0 values to min/max of available data
- Boolean masking by indentation depth
- Proper handling of NaN values

---

## Units and Ranges

**Parameter Units:** Nanometers (nm)  
**Typical Range:** 0-10000 nm (which equals 0-10 micrometers)  
**Input Data:** Assumed to be in meters (SI units)  
**Conversion:** Automatic (m → nm for comparison, original m returned)

## Default Behavior

Without setting fitting region parameters (or with both at 0):
- The entire available indentation range is used for fitting
- No data is excluded
- Backward compatible with existing pipelines
