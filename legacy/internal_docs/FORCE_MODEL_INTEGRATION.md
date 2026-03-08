# Force Model Fitting in SoftMech Designer

## Overview

The SoftMech Designer now supports force model fitting as a standard pipeline step, allowing users to fit mechanical models (like Hertz contact mechanics) to their AFM indentation data after contact point identification.

## Changes Made

### 1. Plugin Discovery
- **Force model plugins** are now automatically discovered from `softmech/plugins/force_models/`
- Currently available: `hertz` (Hertz contact mechanics model)

### 2. Default Pipeline Structure
The default pipeline now consists of:
1. **Filter** (optional preprocessing)
2. **Contact Point** (CP identification)
3. **Force Model** (model fitting) ← **NEW**

### 3. Removed Features (Temporarily)
- **Elasticity spectra** calculation has been removed from the default workflow
  - It was causing issues and needs refinement
  - Indentation data is still calculated automatically after CP detection
  - Users can still manually calculate elasticity spectra if needed via the core API

## Workflow

### Step-by-Step Process

1. **Load Data**: Open an AFM experiment file (JSON or HDF5)

2. **Configure Filtering** (optional):
   - Select filter type (e.g., Savitzky-Golay)
   - Adjust parameters
   - Can add multiple filters

3. **Set Contact Point Detection**:
   - Change algorithm from "none" to desired method
   - Options include: autothresh, nanite variants, etc.
   - Edit parameters as needed

4. **Configure Force Model Fitting** ← **NEW STEP**:
   - Change algorithm from "none" to "hertz"
   - Set Poisson's ratio (default: 0.5)
   - Hertz model fits F(δ) curves to extract Young's modulus

5. **Run Pipeline**:
   - Click "Run Pipeline" button
   - Pipeline executes all steps in sequence
   - After CP detection, indentation data is auto-calculated
   - Force model then fits to the indentation data

6. **View Results**:
   - Visualization shows processed curves
   - Force model parameters stored in curve object
   - Can export data and plots

## Technical Details

### Force Model Execution

When a force model step executes:
1. Requires valid contact point (from CP step)
2. Uses auto-calculated indentation data (δ, F)
3. Calls plugin's `calculate(delta, force, curve=curve)` method
4. Returns fitted parameters (e.g., [Young's modulus])
5. Stores results via `curve.set_force_model_params(params)`

### "none" Placeholder

Steps with `plugin_id="none"` are **skipped** during execution:
- Allows users to design pipelines without all steps configured
- Default pipeline starts with all steps set to "none"
- Users progressively enable steps as needed

### Plugin Interface

Force model plugins must:
- Inherit from `ForceModel` base class
- Implement `calculate(x, y, curve=None)` method
- Implement `theory(x, params, curve=None)` for visualization
- Return fitted parameters as a list or dict

## Example Pipeline JSON

```json
{
  "version": "2.0",
  "metadata": {
    "name": "Default Pipeline",
    "description": "Default pipeline with none placeholders"
  },
  "stages": [
    {
      "name": "preprocessing",
      "description": "Filtering and contact point",
      "steps": [
        {"type": "filter", "plugin_id": "none", "parameters": {}},
        {"type": "contact_point", "plugin_id": "none", "parameters": {}}
      ]
    },
    {
      "name": "analysis",
      "description": "Model fitting",
      "steps": [
        {"type": "force_model", "plugin_id": "none", "parameters": {}}
      ]
    }
  ]
}
```

## Files Modified

1. **main_window.py**:
   - Added force_models plugin discovery
   - Changed default pipeline from elasticity_spectra to force_model

2. **executor.py**:
   - Added "none" skip logic
   - Removed auto-calculation of elasticity spectra after CP
   - Kept indentation auto-calculation for force model fitting

3. **block_pipeline_editor.py**:
   - Already had force_model UI support (no changes needed)

## Future Enhancements

- Add more force models (DMT, JKR, etc.)
- Re-enable elasticity spectra as optional advanced step
- Support elastic model fitting (E vs δ relationship)
- Add visualization of fitted model overlay on data
- Parameter estimation confidence intervals
