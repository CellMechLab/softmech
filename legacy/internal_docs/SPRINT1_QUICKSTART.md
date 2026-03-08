# Sprint 1: Designer UI MVP - Quick Start

## Current Status

✓ UI skeleton created with:
- Main window with menu bar
- File → Open Curve (loads JSON/HDF5)
- File → Save/Load Pipeline (JSON serialization)
- Export Data and Plot buttons (placeholders)
- Status bar with messages
- Plugin registry integrated

## Next Steps (Sprint 1 Deliverables)

### Week 1a: Test the Skeleton (1-2 hours)
```bash
cd softmech
pip install PySide6  # if not already installed
python softmech/ui/designer/main_window.py
```

**What to test:**
- [ ] Window opens and shows "Ready" in status bar
- [ ] File → Open Curve opens file dialog
- [ ] Load tools/synth.json and see status message
- [ ] Plugins are discovered (check console output)
- [ ] File → Save Pipeline prompts to save
- [ ] File → Load Pipeline loads a saved pipeline

### Week 1b: Visualization Widget (4-6 hours)
**Goal:** Add PyQtGraph plot showing complete AFM analysis results

**File:** `softmech/ui/designer/widgets/visualization.py`

**Technology:** PyQtGraph (native Qt, 10-50x faster than matplotlib, GPU-accelerated)

**Features:**
- Create Visualization widget with PyQtGraph PlotWidget embedded
- Tabbed interface with 4 visualization tabs:
  - **Raw**: Original Z vs F data (what was loaded)
  - **Filtered**: Processed force curve after filter stage
  - **Indentation**: Indentation depth δ vs Force (relative to contact point)
  - **Elasticity**: Young's modulus E vs indentation depth (log scale)
- Auto-scale axes with proper unit labeling (μm, nN, Pa)
- Instant responsiveness for real-time updates (slider → redraw < 50ms)
- Show fit quality metrics on plots (R², error bars)
- Gray out tabs for stages that weren't executed (e.g., no Elasticity if force fit invalid)

**Why PyQtGraph:**
✓ 10-50x faster rendering (critical for responsive UI)
✓ Real-time filter updates (slider changes redraw instantly)
✓ Native Qt integration (PySide6 first-class design)
✓ GPU-accelerated (future-proof for batch mode)
✓ Built-in zoom/pan with crosshairs (no toolbar needed)

**Pseudocode:**
```python
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

class VisualizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        
        # Tab 1: Raw curve
        self.plot_raw = pg.PlotWidget()
        self.plot_raw.setLabel('bottom', 'Displacement', units='μm')
        self.plot_raw.setLabel('left', 'Force', units='nN')
        self.plot_raw.showGrid(True, True, 0.3)
        self.plot_raw.setTitle('Raw Force Curve')
        self.tabs.addTab(self.plot_raw, "Raw")
        
        # Tab 2: Filtered curve
        self.plot_filtered = pg.PlotWidget()
        self.plot_filtered.setLabel('bottom', 'Displacement', units='μm')
        self.plot_filtered.setLabel('left', 'Force', units='nN')
        self.plot_filtered.showGrid(True, True, 0.3)
        self.plot_filtered.setTitle('Filtered Force Curve (after filters)')
        self.tabs.addTab(self.plot_filtered, "Filtered")
        
        # Tab 3: Indentation plot
        self.plot_indentation = pg.PlotWidget()
        self.plot_indentation.setLabel('bottom', 'Indentation Depth', units='μm')
        self.plot_indentation.setLabel('left', 'Force', units='nN')
        self.plot_indentation.showGrid(True, True, 0.3)
        self.plot_indentation.setTitle('Indentation: F vs δ')
        self.tabs.addTab(self.plot_indentation, "Indentation")
        
        # Tab 4: Elasticity spectra (log scale)
        self.plot_elasticity = pg.PlotWidget()
        self.plot_elasticity.setLabel('bottom', 'Indentation Depth', units='μm')
        self.plot_elasticity.setLabel('left', "Young's Modulus", units='Pa')
        self.plot_elasticity.setLogMode(y=True)
        self.plot_elasticity.showGrid(True, True, 0.3)
        self.plot_elasticity.setTitle("Elasticity Spectra: E(δ) [Conditional]")
        self.tabs.addTab(self.plot_elasticity, "Elasticity")
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
    
    def update_all(self, result):
        """Update all tabs based on pipeline execution result."""
        # Tab 1: Raw (always available)
        self.plot_raw_curve(result.Z, result.F)
        
        # Tab 2: Filtered (always available after pipeline)
        self.plot_filtered_curve(result.Z_filtered, result.F_filtered)
        
        # Tab 3: Indentation (always available)
        self.plot_indentation_data(result.delta, result.F_indentation)
        
        # Tab 4: Elasticity (only if force fit was valid)
        if hasattr(result, 'E_spectra') and result.E_spectra is not None:
            self.plot_elasticity_spectra(result.delta, result.E_spectra)
            self.tabs.setTabEnabled(3, True)  # Enable tab
        else:
            self.tabs.setTabEnabled(3, False)  # Gray out tab
            self.plot_elasticity.clear()
    
    def plot_raw_curve(self, Z, F):
        """Plot original force vs displacement."""
        self.plot_raw.clear()
        Z_um = Z * 1e6
        F_nN = F * 1e9
        self.plot_raw.plot(Z_um, F_nN, pen=pg.mkPen('b', width=2), name='Raw')
    
    def plot_filtered_curve(self, Z, F):
        """Plot filtered force vs displacement."""
        self.plot_filtered.clear()
        Z_um = Z * 1e6
        F_nN = F * 1e9
        self.plot_filtered.plot(Z_um, F_nN, pen=pg.mkPen('g', width=2), name='Filtered')
    
    def plot_indentation_data(self, delta, F_indentation):
        """Plot indentation depth vs force."""
        self.plot_indentation.clear()
        delta_um = delta * 1e6
        F_nN = F_indentation * 1e9
        # Plot force response in indentation
        self.plot_indentation.plot(delta_um, F_nN, pen=pg.mkPen('r', width=2))
        # Optionally overlay fit
    
    def plot_elasticity_spectra(self, delta, E):
        """Plot elasticity spectra with log scale."""
        self.plot_elasticity.clear()
        delta_um = delta * 1e6
        self.plot_elasticity.plot(delta_um, E, pen=pg.mkPen('purple', width=2))
```

**Integration points:**
- In `main_window.py`: Replace visualization placeholder with VisualizationWidget
- In `main_window.py` `run_pipeline()`: Call `self.visualization.update_all(result)`
- In `properties_panel.py` (Week 1d): Use same visualization widget for live preview on parameter changes

### Week 1c: Pipeline Editor Widget - Flowchart (6-8 hours)
**Goal:** Modern flowchart-style pipeline editor with complete AFM analysis stages

**File:** `softmech/ui/designer/widgets/pipeline_editor.py`

**Technology:** PyQtGraph FlowchartWidget (professional, modern, drag-drop ready)

**Pipeline Structure:**
The complete AFM analysis pipeline has these stages in order:

```
Stage 1: FILTERS (1 or more in sequence)
  [savgol] → [median] → [notch] → ... (user can chain multiple filters)

Stage 2: FIXED ANALYSIS (in order)
  [CP Detection] → [Indentation Calc] → [Force Fit] → [E Spectra*] → [E Fit]
  
  * = E Spectra calculation method is AUTOMATIC & ADAPTIVE:
      - If Force Model = Hertz     → Use Hertz contact mechanics formula
      - If Force Model ≠ Hertz     → Use local fitting window approach
      
      E Spectra is SKIPPED only if Force Fit is invalid
```

**Key Insight: Method-Based, Not Binary**

Unlike simple yes/no conditional logic, the E Spectra calculation **automatically adapts to the force model choice**:

- **Hertz Model**: E(δ) = (π/2) · dF/dδ / A(δ) using contact mechanics
- **Other Models** (linear, power law, sneddon, etc.): E(δ) from local fitting at multiple indentation depths

This follows the PyJibe approach (https://pyjibe.readthedocs.io/en/0.15.4/sec_interface.html) where E(δ) is always calculated but the method depends on what force model user selected.

**Features:**
- Visual flowchart showing all pipeline stages
- Multiple filters supported (user can [+ Add Filter] to chain them)
- Filters flow into CP Detection node
- Fixed analysis nodes in order: CP → Indentation → Force Fitting → E Spectra → E Fitting
- **Smart node info**: Click E Spectra node shows "Using: Contact Mechanics" or "Using: Local Fit Window"
- Conditional skip only based on Force Fit validity (not a rigid yes/no for E)
- Double-click node to edit parameters (pop-up dialog or right sidebar)
- "Run Pipeline" executes the chain intelligently
- "Save Pipeline" exports to JSON with all filter + node parameters
- "Load Pipeline" restores complete pipeline with correct filter count

**Why This Structure:**
✓ Matches actual AFM analysis physics (filters → CP detection → fitting)
✓ Supports realistic pipelines (multiple filters before analysis)
✓ Shows data dependencies (E fitting depends on successful force fit)
✓ **Intelligently adapts E calculation to the force model chosen**
✓ User can visually understand the flow and which stages executed
✓ Foundation for manual parameter tuning (adjust filters, see fit quality)

**Pseudocode:**
```python
from pyqtgraph.flowchart import FlowchartWidget, Node

class PipelineEditor(FlowchartWidget):
    """Visual AFM pipeline with filters, analysis, and adaptive E spectra."""
    
    def __init__(self, registry):
        super().__init__(terminals={
            'CurveIn': {'io': 'in'},
            'ResultOut': {'io': 'out'}
        })
        self.registry = registry
        self.filter_nodes = []  # Can have multiple
        self.force_model = 'hertz'  # User can change this
        self.setup_default_pipeline()
    
    def setup_default_pipeline(self):
        """Create: savgol → CP → Indentation → Hertz → E Spectra → E Const"""
        
        # Stage 1: Default filter
        savgol = self.create_filter_node('savgol', pos=(100, 0))
        self.add_filter_node(savgol, name='filter_savgol')
        
        # Stage 2-6: Fixed analysis pipeline
        cp_node = self.create_analysis_node('autothresh', pos=(300, 0))
        indent_node = self.create_analysis_node('indentation', pos=(500, 0))
        ffit_node = self.create_analysis_node('hertz', pos=(700, 0))
        
        # E SPECTRA: Note - method will be chosen automatically
        espectra_node = self.create_adaptive_e_spectra_node(
            pos=(900, 0),
            depends_on='force_fitting'
        )
        
        efit_node = self.create_analysis_node(
            'elastic_constant', pos=(1100, 0),
            depends_on='elasticity_spectra'
        )
        
        self.addNode(cp_node, name='cp_detection')
        self.addNode(indent_node, name='indentation')
        self.addNode(ffit_node, name='force_fitting')
        self.addNode(espectra_node, name='elasticity_spectra')
        self.addNode(efit_node, name='elastic_fitting')
    
    def create_adaptive_e_spectra_node(self, pos, depends_on):
        """Create E Spectra node with ADAPTIVE calculation method."""
        
        class AdaptiveESpectraNode(Node):
            nodeName = "E Spectra (Adaptive)"
            
            def __init__(self, name):
                terminals = {
                    'In_indentation': {'io': 'in'},
                    'Out': {'io': 'out'}
                }
                Node.__init__(self, name, terminals=terminals)
                self.should_execute = True
            
            def process(self, In_indentation, **kwargs):
                if not self.should_execute:
                    return {'Out': None}  # Skip if force fit invalid
                
                # Automatically choose method based on force model
                method = self.get_e_spectra_method()
                
                if method == 'hertz_contact_mechanics':
                    # Use contact mechanics formula
                    e_spectra = self.calculate_hertz_e_spectra(In_indentation)
                else:  # 'local_fitting_window'
                    # Use local fitting approach
                    e_spectra = self.calculate_local_fit_e_spectra(In_indentation)
                
                return {'Out': e_spectra}
            
            def get_e_spectra_method(self):
                """Determine which E spectra method to use."""
                # This would look at the force model selected earlier
                # For now: simplified logic
                force_model = kwargs.get('force_model', 'hertz')
                if force_model == 'hertz':
                    return 'hertz_contact_mechanics'
                else:
                    return 'local_fitting_window'
            
            def calculate_hertz_e_spectra(self, indentation_data):
                """Hertz contact mechanics approach."""
                # dF/dδ → Contact Area A(δ) → E(δ) = (π/2) · dF/dδ / A
                pass
            
            def calculate_local_fit_e_spectra(self, indentation_data):
                """Local fitting window approach."""
                # For each δ: fit model locally → extract E_i
                pass
        
        return AdaptiveESpectraNode("E Spectra")
    
    def execute_pipeline(self, input_curve):
        """Execute pipeline with adaptive E spectra selection."""
        
        # Stage 1: All filters in sequence
        filtered = input_curve
        for f_node in self.filter_nodes:
            filtered = f_node.process(filtered)
        
        # Stages 2-4: Fixed analysis (always execute)
        cp_data = self.nodes['cp_detection'].process(filtered)
        indent_data = self.nodes['indentation'].process(cp_data)
        ffit_data = self.nodes['force_fitting'].process(indent_data)
        
        # Stages 5-6: Adaptive E Analysis (skip if force fit invalid)
        if self._is_force_fit_valid(ffit_data):
            # E Spectra method is chosen automatically inside the node
            espectra_data = self.nodes['elasticity_spectra'].process(indent_data)
            result = self.nodes['elastic_fitting'].process(espectra_data)
        else:
            result = ffit_data  # Stop at force fitting
        
        return result
    
    def _is_force_fit_valid(self, ffit_result):
        """Check if force fitting is valid enough for E analysis."""
        r2 = ffit_result.get('R2', 0)
        residuals_ok = abs(ffit_result.get('residuals_mean', 0)) < 1e-10
        return r2 > 0.90 and residuals_ok
```

**Integration with main_window.py:**
```python
# In main_window.py
from softmech.ui.designer.widgets.pipeline_editor import PipelineEditor

def _create_left_panel(self):
    self.pipeline_editor = PipelineEditor(self.registry)
    self.left_layout.addWidget(self.pipeline_editor)

def run_pipeline(self):
    if self.current_curve is None:
        return
    
    result = self.pipeline_editor.execute_pipeline(self.current_curve)
    
    # Update visualization with all stages
    self.visualization.plot_filtered_curve(result.F_filtered)
    self.visualization.plot_indentation(result.delta, result.F_indentation)
    
    # E Spectra shown only if force fit was valid AND E spectra succeeded
    if hasattr(result, 'E_spectra') and result.E_spectra is not None:
        self.visualization.plot_elasticity_spectra(result.delta, result.E_spectra)
```

**Future Enhancements (Sprint 2+):**
- [ ] [+ Add Filter] button to dynamically add more filters
- [ ] Right-click node to delete (for filters)
- [ ] Color-code nodes by category (Filter=blue, Analysis=green)
- [ ] Visual indicator of E Spectra calculation method
- [ ] Parameter panel in right sidebar (not modal dialog)

**Pseudocode:**
```python
from pyqtgraph.flowchart import FlowchartWidget, Node

class PipelineEditor(FlowchartWidget):
    """Visual AFM pipeline with filters, analysis, and conditional stages."""
    
    def __init__(self, registry):
        super().__init__(terminals={
            'CurveIn': {'io': 'in'},
            'ResultOut': {'io': 'out'}
        })
        self.registry = registry
        self.filter_nodes = []  # Can have multiple
        self.setup_default_pipeline()
    
    def setup_default_pipeline(self):
        """Create: savgol → CP → Indentation → Hertz → E Spectra → E Const"""
        
        # Stage 1: Default filter
        savgol = self.create_filter_node('savgol', pos=(100, 0))
        self.add_filter_node(savgol, name='filter_savgol')
        
        # Stage 2-6: Fixed analysis pipeline
        cp_node = self.create_analysis_node('autothresh', pos=(300, 0))
        indent_node = self.create_analysis_node('indentation', pos=(500, 0))
        ffit_node = self.create_analysis_node('hertz', pos=(700, 0))
        espectra_node = self.create_analysis_node(
            'elasticity_spectra', pos=(900, 0), 
            conditional=True, depends_on='force_fitting'
        )
        efit_node = self.create_analysis_node(
            'constant', pos=(1100, 0),
            conditional=True, depends_on='elasticity_spectra'
        )
        
        self.addNode(cp_node, name='cp_detection')
        self.addNode(indent_node, name='indentation')
        self.addNode(ffit_node, name='force_fitting')
        self.addNode(espectra_node, name='elasticity_spectra')
        self.addNode(efit_node, name='elastic_fitting')
    
    def add_filter_node(self, filter_node, name):
        """Append a filter node to the filter chain."""
        self.filter_nodes.append(filter_node)
        x_pos = 100 + len(self.filter_nodes) * 50  # Chain horizontally
        filter_node.setPos((x_pos, 0))
        self.addNode(filter_node, name=name)
    
    def execute_pipeline(self, input_curve):
        """Execute pipeline with conditional logic for E fitting."""
        
        # Stage 1: All filters in sequence
        filtered = input_curve
        for f_node in self.filter_nodes:
            filtered = f_node.process(filtered)
        
        # Stages 2-4: Fixed analysis (always execute)
        cp_data = self.nodes['cp_detection'].process(filtered)
        indent_data = self.nodes['indentation'].process(cp_data)
        ffit_data = self.nodes['force_fitting'].process(indent_data)
        
        # Stages 5-6: Conditional (skip if force fit invalid)
        if self._is_force_fit_valid(ffit_data):
            espectra_data = self.nodes['elasticity_spectra'].process(indent_data)
            result = self.nodes['elastic_fitting'].process(espectra_data)
        else:
            result = ffit_data  # Stop at force fitting
        
        return result
    
    def _is_force_fit_valid(self, ffit_result):
        """Check R² and residuals to decide if E fitting should run."""
        r2 = ffit_result.get('R2', 0)
        residuals_ok = abs(ffit_result.get('residuals_mean', 0)) < 1e-10
        return r2 > 0.95 and residuals_ok
```

**Integration with main_window.py:**
```python
# In main_window.py
from softmech.ui.designer.widgets.pipeline_editor import PipelineEditor

def _create_left_panel(self):
    self.pipeline_editor = PipelineEditor(self.registry)
    self.left_layout.addWidget(self.pipeline_editor)

def run_pipeline(self):
    if self.current_curve is None:
        return
    
    result = self.pipeline_editor.execute_pipeline(self.current_curve)
    
    # Update visualization with all stages
    self.visualization.plot_filtered_curve(result.F_filtered)
    self.visualization.plot_indentation(result.delta, result.F_indentation)
    
    # Only show E Spectra if force fit was valid
    if hasattr(result, 'E_spectra'):
        self.visualization.plot_elasticity_spectra(result.delta, result.E_spectra)
```

**Future Enhancements (Sprint 2+):**
- [ ] [+ Add Filter] button to dynamically add more filters
- [ ] Right-click node to delete (for filters)
- [ ] Color-code nodes by category (Filter=blue, Analysis=green)
- [ ] Visual conditional indicator (grayed out if skipped, warning icon)
- [ ] Parameter panel in right sidebar (not modal dialog)

### Week 1d: Basic Filter Control (3-4 hours)
**Goal:** Add savgol filter with parameter adjustment

**File:** `softmech/ui/designer/widgets/properties_panel.py`

**Features:**
- Use magicgui to auto-generate parameter widgets
- Parameter changes trigger live computation
- Show before/after curve overlay

**Pseudocode:**
```python
from magicgui import magicgui

class FilterPropertiesPanel(QWidget):
    def __init__(self, registry):
        savgol_plugin = registry.get("savgol")
        
        # Auto-create UI from type hints
        @magicgui(window_size={"value": 25, "min": 1, "max": 500},
                  polyorder={"value": 3, "min": 1, "max": 7})
        def filter_params(window_size: float, polyorder: int):
            # Update plugin
            savgol_plugin.set_parameter("window_size", window_size)
            savgol_plugin.set_parameter("polyorder", polyorder)
            self.on_params_changed()
```

---

## Sprint 1 Success Criteria

**By end of Week 1:**
- [ ] Designer window starts without errors
- [ ] Can load tools/synth.json
- [ ] Raw curve data displays instantly in PyQtGraph plot
- [ ] Zoom/pan interactions are smooth and responsive
- [ ] **Flowchart pipeline editor shows complete AFM analysis pipeline**
  - [ ] Filter stage (savgol visible, can add more filters)
  - [ ] Fixed analysis stages: CP → Indentation → Force Fit → E Spectra → E Fit
  - [ ] E Spectra method shows as "Contact Mechanics" (for Hertz) or "Local Fit" (for others)
- [ ] Can run complete pipeline from flowchart
- [ ] Filtered curve, indentation, and (if force fit valid) elasticity spectra display
- [ ] E Spectra calculation automatically adapts to force model choice
- [ ] Can save and load complete pipeline with filter count and all parameters
- [ ] No visual lag when interacting with flowchart or updating plots

**Definition of Done (Demo):**
```
1. User opens Designer
2. File → Open: tools/synth.json
3. Sees raw F-Z curve in PyQtGraph visualization (instant, smooth zoom/pan)
4. LEFT PANEL shows complete flowchart:
   [savgol] → [CP Detection] → [Indentation] → [Hertz Fit] → [E Spectra*] → [E Fit]
   (* note on E Spectra showing "Contact Mechanics Method")
5. Clicks "Run Pipeline"
6. RIGHT PANEL shows all results:
   - Raw curve tab
   - Filtered curve (after savgol)
   - Indentation (δ vs F)
   - Force fit quality (R² shown)
   - Elasticity spectra (E vs δ, log scale) [only if Hertz fit valid]
7. Double-clicks E Spectra node, sees "Calculation Method: Contact Mechanics"
8. Changes Force Model to "linear", reruns
9. E Spectra node now shows "Calculation Method: Local Fitting Window"
10. Saves pipeline (File → Save Pipeline), reloads it
11. Flowchart remains responsive (smooth drag, no lag)
12. If force fit has low R², E Spectra is skipped with warning
```

---

## Dependencies to Install

```bash
pip install PySide6 pyqtgraph magicgui
```

**Note:** matplotlib is optional (only needed for report export, not for UI visualization in Sprint 1).

## File Checklist

- [x] `softmech/ui/__init__.py` - UI package marker
- [x] `softmech/ui/designer/__init__.py` - Designer package
- [x] `softmech/ui/designer/main_window.py` - Main window skeleton
- [x] `softmech/ui/designer/widgets/__init__.py` - Widgets package
- [ ] `softmech/ui/designer/widgets/visualization.py` - Plot widget (TODO)
- [ ] `softmech/ui/designer/widgets/pipeline_editor.py` - Pipeline steps (TODO)
- [ ] `softmech/ui/designer/widgets/properties_panel.py` - Parameter controls (TODO)
- [x] `softmech/ui/analyzer/__init__.py` - Analyzer package marker
- [x] `softmech/ui/cli/__init__.py` - CLI package marker

---

## Development Workflow

1. **Test current skeleton:**
   ```bash
   python softmech/ui/designer/main_window.py
   ```

2. **Add visualization widget** and integrate:
   ```python
   # In main_window.py _create_right_panel()
   from softmech.ui.designer.widgets.visualization import VisualizationWidget
   viz = VisualizationWidget()
   layout.addWidget(viz)
   ```

3. **Test with real data:**
   ```python
   # In main_window.py open_curve()
   window.visualization.plot_raw_curve(Z, F)
   ```

4. **Add pipeline editor** similarly

5. **Iterate until all 4 widgets work together**

---

## Notes

**Complete AFM Analysis Pipeline:**

The pipeline has 6 stages executing in order:

1. **Filters** (Stage 1, 1+ nodes)
   - Savitzky-Golay (default), median, notch, etc.
   - Multiple filters can chain in sequence
   - Purpose: Reduce noise in raw force data

2. **Contact Point Detection** (Stage 2, fixed)
   - Autothresh method
   - Purpose: Find where probe first touches sample

3. **Indentation Depth Calculation** (Stage 3, fixed)
   - Convert Z displacement → δ indentation using spring constant
   - Formula: δ = (Z - Z_cp) - (F - F_cp) / k
   - Purpose: Account for cantilever deflection

4. **Force Model Fitting** (Stage 4, fixed)
   - Hertz contact mechanics (default)
   - Fit F vs δ curve, extract fit quality (R²)
   - Purpose: Determine sample stiffness, check data quality

5-6. **Elasticity Analysis** (Stages 5-6, CONDITIONAL)
   - **E Spectra Calculation**: dF/dδ → Young's modulus using contact area
   - **E Fitting**: Fit elastic model (constant E, sigmoid, etc.)
   - **ONLY EXECUTE IF**: Force fit is valid (R² > 0.95 and residuals acceptable)
   - **SKIP IF**: Force fit is poor, making E extraction unreliable

**Conditional Execution:**
The flowchart shows stages 5-6 with special marking because they skip if the force fit (stage 4) is invalid. This is physics-driven: if we can't trust the force model fit, we can't trust E values derived from it.

**Visualization Updates:**
The visualization tabs reflect this:
- Tabs 1-3 (Raw, Filtered, Indentation) always show
- Tab 4 (Elasticity) is grayed out if conditional E analysis was skipped

**PyQtGraph vs matplotlib & Flowchart:**
- **Visualization (Week 1b)**: PyQtGraph for instant zoom/pan, real-time updates
- **Pipeline Editor (Week 1c)**: PyQtGraph Flowchart for professional node-graph UI
- See `PLOTTING_COMPARISON.py` and `PIPELINE_ARCHITECTURE.md` for full design rationale

**Sprint 1 Timeline Adjusted:**
- Week 1a: Test skeleton (1-2 hrs) ✓
- Week 1b: PyQtGraph visualization (4-6 hrs) ✓
- Week 1c: PyQtGraph flowchart editor with filters + conditional stages (6-8 hrs) [uses more time due to complexity, but essential for proper AFM support]
- Week 1d: Properties panel + magicgui (3-4 hrs)

Total: ~16-20 hours (produces professional AFM analysis UI)

**Other Implementation Details:**
- All widgets should have `.curve_changed()` signal to propagate updates
- Use `QThread` for long-running computations (pipeline execution)
- Keep core logic separate from UI (already done ✓)
- Test with `tools/synth.json` as reference dataset (40 known curves)
- Flowchart JSON serialization must round-trip with PipelineDescriptor
- Ensure filter chaining actually executes in sequence (filter 1 output → filter 2 input)
- Conditional skip logic must be visible/indicated to user
