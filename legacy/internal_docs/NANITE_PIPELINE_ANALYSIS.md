# Nanite Pipeline Architecture Analysis

## Executive Summary

**nanite is a fully-featured AFM analysis library** with a mature, modular pipeline system. Key finding: **Their pipeline architecture is highly compatible with softmech's design**, and we can potentially reuse significant portions of their implementations.

---

## 1. Nanite Core Classes & API

### Main Classes (in `src/nanite/indent.py`)

```python
class Indentation(afmformats.AFMForceDistance):
    """Wraps raw AFM data with analysis capabilities"""
    
    # Key properties:
    preprocessing: list  # preprocessing step identifiers
    preprocessing_options: dict  # options for each step
    fit_properties: FitProperties  # fitting results dictionary
    _preprocessing_details: dict  # preprocessing details (debug info)
```

### Pipeline Flow
```
IndentationGroup
    ↓
Indentation  ← Raw AFM data wrapper
    ↓
.apply_preprocessing()  ← Apply filtering/preprocessing steps
    ↓
.estimate_contact_point_index()  ← Detect contact point
    ↓
.fit_model()  ← Fit force model
    ↓
.compute_emodulus_mindelta()  ← Calculate E(δ) spectra
    ↓
.rate_quality()  ← Quality rating (machine learning)
```

---

## 2. Preprocessing System (`src/nanite/preproc.py`)

### Architecture: Decorator-Based Pipeline

nanite uses **Python decorators** to register preprocessing methods:

```python
@preprocessing_step(
    identifier="correct_tip_offset",
    name="Estimate contact point",
    steps_required=["compute_tip_position"],
    steps_optional=["correct_force_offset"],
    options=[
        {"choices": ["gradient_zero_crossing", "fit_constant_line", 
                     "fit_constant_polynomial", "fit_line_polynomial",
                     "frechet_direct_path", "deviation_from_baseline"]}
    ]
)
def preproc_correct_tip_offset(apret, method="deviation_from_baseline"):
    """Correct tip offset (contact point detection)"""
    # Implementation...
```

### Available Preprocessing Steps

From test files and source code, nanite supports:

1. **`compute_tip_position`** - Basic preprocessing: compute Z_tip from piezo position
2. **`correct_force_offset`** - Remove force baseline offset
3. **`correct_force_slope`** - Remove force slope due to tilted baseline
4. **`correct_tip_offset`** (6 methods for contact point):
   - `gradient_zero_crossing` - Gradient-based CP detection
   - `fit_constant_line` - Constant baseline fitting
   - `fit_constant_polynomial` - Polynomial baseline fitting
   - `fit_line_polynomial` - Line + polynomial baseline
   - `frechet_direct_path` - **Fréchet distance method** (robust!)
   - `deviation_from_baseline` - **recommended method** (DEFAULT)
5. **`correct_split_approach_retract`** - Handle approach/retract segments
6. **`smooth_height`** - Smooth height data
7. More specialized methods available

### Control Structure

```python
# Step 1: Apply preprocessing with options
idnt.apply_preprocessing(
    preprocessing=["compute_tip_position", "correct_force_offset", 
                   "correct_tip_offset", "correct_split_approach_retract"],
    options={
        "correct_tip_offset": {"method": "frechet_direct_path"}
    }
)

# Step 2: Access contact point index
cp_index = idnt.estimate_contact_point_index(
    method="deviation_from_baseline"
)

# Step 3: Preprocessing details available for debugging
details = idnt.apply_preprocessing(..., ret_details=True)
# Returns dict with plotting info via 'plot <name>' keys
```

---

## 3. Fitting System (`src/nanite/fit.py`)

### IndentationFitter Class

```python
class IndentationFitter(object):
    """Fit force-distance curves to contact mechanics models"""
    
    def __init__(self, idnt, **kwargs):
        # Takes preprocessed Indentation object
        # Kwargs: model_key, params_initial, range_x, range_type,
        #         weight_cp, segment, x_axis, y_axis, gcf_k,
        #         optimal_fit_edelta, optimal_fit_num_samples
        
    def fit(self):
        """Perform the actual fitting"""
        
    @staticmethod
    def compute_emodulus_vs_mindelta(callback=None):
        """Compute E(δ) - elastic modulus vs indentation depth"""
        # Systematic parameter sweep to get E(δ) curve
        
    @staticmethod
    def compute_opt_mindelta(emoduli, indentations):
        """Find optimal indentation depth from plateau in E(δ)"""
```

### Key Features
- **Contact point weighting**: `weight_cp` parameter suppresses residuals near CP
- **Optimal fit detection**: Searches for plateau in E(δ) curve
- **Two-pass fitting**: For "relative cp" range_type (iterative CP refinement)
- **Geometrical correction factor**: `gcf_k` for non-single-contact geometries

---

## 4. Rating System (`src/nanite/rate/`)

### Quality Assessment Pipeline

nanite implements **~70 computed features** analyzed with machine learning:

```python
class IndentationFeatures(object):
    """Compute 70+ features from fitted AFM data"""
    
    @staticmethod
    def compute_features(idnt, which_type="all", names=None, ret_names=False):
        """Extract all features from curve"""
        
    @classmethod
    def get_feature_names(cls, which_type="all", names=None):
        """List available features"""
        # which_type: "all", "bool", "continuous"
        
class IndentationRater(IndentationFeatures):
    """Apply ML classifier to rating"""
    
    def rate(self, samples=None, datasets=None):
        """Rate quality (0-10 scale, -1 if unfitted)"""
        
    @staticmethod
    def get_training_set_path(label="zef18"):
        """Get path to training sets (default: zef18 zebrafish data)"""
```

### Quality Features Examples

Binary features (True/False):
- `feat_bin_apr_spikes_count` - Spike detection during indentation
- `feat_bin_size` - Curve size check
- `feat_bin_cp_position` - Contact point validity

Continuous features (float 0-1):
- `feat_con_apr_flatness` - Baseline flatness
- `feat_con_idt_monotony` - Monotonicity in indentation
- `feat_con_idt_sum` - Residual sum in indentation
- `feat_con_cp_curvature` - Curvature at contact point
- `feat_con_apr_sum` - Residual sum in approach
- ~60 more...

### Built-in Training Sets

- **zef18**: Zebrafish spinal cord sections (default, 2018)
- **Custom**: User can import trained models

---

## 5. Contact Point Detection Deep Dive

### Available Methods (from `src/nanite/poc.py`)

All available via `idnt.estimate_contact_point_index(method=...)`

1. **`gradient_zero_crossing`**
   - Finds zero-crossing in force curve gradient
   - Fast, simple, susceptible to noise

2. **`fit_constant_line`**
   - Fits constant to baseline
   - Finds intersection with curve
   - Good for clean baselines

3. **`fit_constant_polynomial`**
   - Polynomial baseline fitting
   - More robust to tilted baselines

4. **`fit_line_polynomial`**
   - Combined line + polynomial approach
   - Intermediate complexity

5. **`frechet_direct_path`** ⭐ **ROBUST METHOD**
   - Uses Fréchet distance to direct path
   - Computes normalized coordinates (0,0)→(1,1)
   - Finds point with max distance to diagonal
   - **Robust to tilted baselines, good initial guess**
   - Preprocessing: `["clip_approach"]` required

6. **`deviation_from_baseline`** ⭐ **RECOMMENDED** (default)
   - Sophisticated baseline deviation analysis
   - Adaptive thresholding
   - Best empirical performance

### Test Validation Results

From `tests/test_poc.py`:

```python
@pytest.mark.parametrize("method,contact_point", [
    ["gradient_zero_crossing", 1895],
    ["fit_constant_line", 1919],
    ["fit_constant_polynomial", 1898],
    ["fit_line_polynomial", 1899],
    ["frechet_direct_path", 1903],
    ["deviation_from_baseline", 1908],  # Default, best
])
def test_poc_estimation_via_indent(method, contact_point):
    # All methods tested against known JPK Force curve
```

---

## 6. Model System (`src/nanite/model/`)

### Available Models

Through nanite.model.models_available:

**Hertz Models** (contact mechanics):
- `hertz_para` - **Hertz paraboloidal** (parabola)
- `hertz_cone` - Cone geometry
- `hertz_pyr3s` - Three-sided pyramid

**Sneddon Models** (generalized contact mechanics):
- `sneddon_spher` - Sneddon sphere
- `sneddon_spher_approx` - Approximation

**Other Models**:
- `power_law` - Power-law model
- `LinearModel` - Linear fit
- Custom user models via extensions

### Model Parameters

Each model has:
- `parameter_keys` - List of fitted parameters
- `parameter_names` - Human-readable names
- `parameter_units` - SI units
- `valid_axes_x`, `valid_axes_y` - Data axis requirements
- Ancillary parameters (computed, not fitted)

---

## 7. Data Export & Serialization

### Export Capabilities

```python
idnt.export_data(path)  # Tab-separated values with metadata
```

### Cached Properties

```python
# Fit results stored in fit_properties dict:
fit_properties = {
    "model_key": str,
    "params_initial": lmfit.Parameters,
    "params_fitted": lmfit.Parameters,
    "params_ancillary": dict,
    "preprocessing": list,
    "preprocessing_options": dict,
    "success": bool,
    "hash": str,  # For caching/reuse
    "segment": int,
    "weight_cp": float,
    "range_x": tuple,
    "range_type": str,
    "optimal_fit_E_array": ndarray,  # E(δ) curve
    "optimal_fit_delta_array": ndarray,
    "optimal_fit_edelta": float,  # Optimal indentation depth
    # ... many more
}
```

---

## 8. Comparison: softmech vs nanite

| Feature | softmech | nanite | Compatibility |
|---------|----------|--------|---------------|
| **Preprocessing** | Custom (starting) | 7+ built-in | Can wrap nanite |
| **Contact Point** | 1 method (autothresh) | 6 methods | Can adapt all |
| **Force Models** | Hertz only | 6+ models | Can extend |
| **E Spectra** | Custom implementation | compute_emodulus_mindelta() | Can use directly |
| **E Fitting** | Custom (planned) | Via models | Can extend |
| **Quality Rating** | Manual (R²) | ML-based (70 features) | Can integrate training sets |
| **Pipeline Control** | Flowchart (planned) | List-based (fixed order) | Different paradigm |
| **File I/O** | JSON (tools/synth.json) | HDF5, JPK, CSV | Can map formats |
| **UI** | PySide6 (building) | PyQt6 (mature) | Code reuse possible |

---

## 9. Integration Opportunities

### Option A: Direct Reuse (RECOMMENDED)
```python
# Use nanite's preprocessing directly
from nanite import load_group
from nanite.preproc import apply

group = load_group("data.jpk-force")
idnt = group[0]

# Apply softmech pipeline but use nanite preprocessing
idnt.apply_preprocessing(
    ["compute_tip_position", "correct_force_offset", "correct_tip_offset"],
    options={"correct_tip_offset": {"method": "frechet_direct_path"}}
)

# Then use softmech's custom E spectra calculation
```

### Option B: Wrapper Integration
```python
# protocols/cpoint/nanite_methods.py
from nanite.poc import compute_poc

class NaniteContactPointDetector:
    METHODS = ["gradient_zero_crossing", "fit_constant_line", 
               "frechet_direct_path", "deviation_from_baseline"]
    
    @staticmethod
    def detect(force, method="deviation_from_baseline"):
        cp_index = compute_poc(force=force, method=method)
        return cp_index
```

### Option C: Hybrid Approach
```python
# Use nanite for preprocessing and contact point
# Use softmech for custom E(δ) calculation and flowchart UI

idnt = Indentation(data, metadata)
idnt.apply_preprocessing(...)  # nanite
cp = idnt.estimate_contact_point_index()  # nanite

# Custom softmech E spectra
e_spectra = softmech.calculate_e_spectra_adaptive(
    force=idnt["force"],
    indentation=indentation_array,
    force_model=user_selected_model
)
```

---

## 10. Code Organization Lessons from nanite

### Decorator Pattern for Extensibility
```python
@preprocessing_step(identifier="...", name="...")
def preproc_custom(...):
    pass  # Auto-registered in preprocessing registry
```

### Feature-Based Architecture
- Separate modules: `indent.py`, `fit.py`, `preproc.py`, `poc.py`, `rate/`, `model/`
- Each is independently importable
- Clear separation of concerns

### Documentation in Tests
- Comprehensive test coverage (~70 test files)
- Tests serve as usage examples
- Test parametrization shows all method combinations

---

## 11. Recommendations for softmech

### SHORT TERM (Week 1-2)
1. **Adopt nanite's contact point methods**: Replace `autothresh` with wrapper
   - Minimal code (~50 lines)
   - Immediate 6x more CP detection methods
   - Tested, validated approach

2. **Use nanite's preprocessing system**: Import `preproc` functions
   - Reuse force/tip offset correction
   - Reuse segment handling
   - Minimal learning curve

### MEDIUM TERM (Week 3-4)
3. **Extend softmech flowchart to show nanite methods**
   - Add dropdown for CP method selection
   - Add preprocessing chain builder (nanite-style)
   - Maintain softmech's flowchart paradigm (more visual than nanite's list)

4. **Keep softmech's unique E spectra calculation**
   - Nanite's `compute_emodulus_mindelta()` is systematic sweep
   - Softmech's adaptive method (Hertz vs local fit) is more sophisticated
   - Can use both: nanite for data availability, softmech for physics

### LONG TERM (Week 5+)
5. **Evaluate ML-based quality rating**
   - Softmech currently: R² only
   - Nanite: 70-feature ML classifier
   - Could train softmech's own training sets with user annotations

6. **Extend model zoo**
   - Soft mech: Hertz only
   - Nanite: 6+ models
   - Easy integration: nanite.model.models_available

---

## 12. Potential Issues & Solutions

### Issue 1: Preprocessing Step Dependencies
**Problem**: Preprocessing steps have `steps_required` dependencies

**Solution**: Use nanite's built-in `autosort()` function
```python
from nanite.preproc import autosort
sorted_steps = autosort(user_selected_steps)
```

### Issue 2: Data Format Conversion
**Problem**: nanite expects `afmformats.AFMForceDistance`, softmech uses raw arrays

**Solution**: Create lightweight adapter
```python
class SoftmechToNaniteAdapter:
    def __init__(self, Z, F, metadata):
        # Wrap in AFMForceDistance format
        self.afm_data = create_afm_force_distance(Z, F, metadata)
```

### Issue 3: Preprocessing Details & Debugging
**Problem**: Nanite's `ret_details=True` returns plotting info for visualization

**Solution**: Pass through to softmech UI
```python
details = idnt.apply_preprocessing(..., ret_details=True)
# details contains "plot correct_tip_offset" info for visualization
```

---

## Summary Table: CP Detection Methods

| Method | Speed | Robustness | Notes |
|--------|-------|-----------|-------|
| gradient_zero_crossing | ⭐⭐⭐ | ⭐ | Simple, noisy |
| fit_constant_line | ⭐⭐ | ⭐⭐ | Good baseline |
| fit_constant_polynomial | ⭐⭐ | ⭐⭐⭐ | Polynomial baseline |
| fit_line_polynomial | ⭐ | ⭐⭐⭐ | Combined approach |
| **frechet_direct_path** | ⭐⭐⭐ | ⭐⭐⭐⭐ | **Best robust method** |
| **deviation_from_baseline** | ⭐⭐ | ⭐⭐⭐⭐⭐ | **Default, best empirical** |

---

## Next Steps

**Immediate action**: Create wrapper for nanite CP methods in `protocols/cpoint/nanite_methods.py`

**Then**: Integrate into softmech's flowchart pipeline editor as CP method selector dropdown

**Finally**: Evaluate sharing more preprocessing/fitting infrastructure
