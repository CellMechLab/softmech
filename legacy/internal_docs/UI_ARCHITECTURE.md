# SoftMech UI Architecture - Agile Development Plan

## Executive Summary

Three complementary UI layers built on the validated core infrastructure:
1. **Designer UI** - Interactive pipeline builder (PySide6)
2. **Batch Analyzer** - Bulk processing with statistics (PySide6)
3. **CLI** - Command-line interface for automation (Click)

---

## Phase 1: Designer UI (MVP - Weeks 1-2)

### Purpose
Let users design, test, and save AFM analysis pipelines interactively with live visualization.

### Technology Stack
- **PySide6** - Qt 6 GUI framework
- **magicgui** - Auto-generate parameter widgets from type hints
- **matplotlib** - Embedded curve visualization
- **JSON** - Pipeline serialization (already supported)

### MVP Features (Phase 1)

#### 1. **Project/Dataset Management**
- [ ] Open single AFM curve (JSON or HDF5)
- [ ] View curve in plot (Z-F raw data)
- [ ] Show curve metadata (spring constant, tip geometry, filename)

#### 2. **Interactive Pipeline Builder**
- [ ] Drag-and-drop filter application (start with savgol only)
- [ ] Live parameter adjustment with instant preview
- [ ] Show before/after comparison
- [ ] Auto-detect and apply contact point (autothresh)
- [ ] Calculate indentation automatically
- [ ] Display elasticity spectra

#### 3. **Pipeline Management**
- [ ] Save pipeline as JSON
- [ ] Load saved pipeline
- [ ] Show processing history for current curve

#### 4. **Results Visualization**
- [ ] Original F-Z curve
- [ ] Filtered curve overlay
- [ ] Indentation (δ) vs. Force
- [ ] Elasticity spectra E(δ)
- [ ] Export plots as PNG

#### 5. **Export Results**
- [ ] Export curve data (CSV: Z, F, δ, E)
- [ ] Export processing metadata

#### 6. **Plugin Test Bench (Developer Tool)**
- [ ] Dedicated UI to test plugins on a single curve
- [ ] Live parameter editing with immediate recompute
- [ ] Diagnostic overlays (derivative, baseline fit, thresholds)
- [ ] Plot raw vs processed vs diagnostic signals
- [ ] Export diagnostic plots for documentation

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  SoftMech Designer - pipeline_v1.json                   │
├─────────────────────────────────────────────────────────┤
│ [Open] [Save] [Save As]  [Run Pipeline]  File: curve1  │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  Pipeline Steps      │      Visualization               │
│  ────────────────    │                                  │
│  1. Filter           │   [Tab: Raw] [Tab: Filtered]     │
│     - savgol         │   [Tab: Indentation]             │
│     - window: 25nm   │   [Tab: Elasticity]              │
│     - polyorder: 3   │                                  │
│     [▼] [X]          │   ┌────────────────────────┐    │
│                      │   │                        │    │
│  2. Contact Point    │   │   Force (N)            │    │
│     - autothresh     │   │        │      ╱╱╱╱     │    │
│     - zero_range: 500│   │        │   ╱╱        │    │
│     [▼] [X]          │   │        │╱╱           │    │
│                      │   │  ──────┼──────────    │    │
│  3. Indentation      │   │     Displacement (m) │    │
│     [✓] computed     │   │                      │    │
│                      │   └────────────────────────┘    │
│  4. Elasticity       │                                  │
│     [✓] computed     │   E range: 4.2 - 5.1 kPa       │
│                      │   δ range: 0 - 7 μm             │
│  [+ Add Step]        │   R²: 0.998                      │
│  [Clear All]         │                                  │
│                      │  [Export Data] [Export Plot]    │
└──────────────────────┴──────────────────────────────────┘
```

### Implementation Structure

```
softmech/ui/
├── designer/
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── pipeline_editor.py  # Left panel: pipeline steps
│   │   ├── visualization.py    # Right panel: plots
│   │   ├── properties_panel.py # Parameter editing with magicgui
│   │   ├── plugin_lab.py        # Plugin Test Bench (debugging UI)
│   │   └── status_bar.py
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── open_curve.py       # File open dialog
│   │   ├── save_pipeline.py    # Save dialog
│   │   └── export_dialog.py    # Export results
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pipeline_model.py   # UI representation of pipeline
│   │   └── visualization_data.py
│   └── styles/
│       ├── __init__.py
│       └── dark.qss            # Optional: custom stylesheet
├── __init__.py
└── resources/                   # Icons, images
```

### Data Flow

```
┌──────────────┐
│  Load Curve  │
│   (JSON/H5)  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Raw Data (Curve obj)    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐    ┌──────────────────┐
│  Apply Step 1: Filter    │◄──│ Get user params  │
│  (plugin.calculate())    │    │ from UI controls │
└──────┬───────────────────┘    └──────────────────┘
       │
       ▼ (step updates curve data)
┌──────────────────────────┐
│  Apply Step 2: Contact Pt│
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Apply Step 3: Indentation
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Apply Step 4: Elasticity │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Render all 4 plots       │
│ Update statistics        │
└──────────────────────────┘
```

---

## Phase 2: Batch Analyzer (MVP - Weeks 3-4)

### Purpose
Process multiple curves with the same pipeline, compare results, extract statistics.

### MVP Features

#### 1. **Batch Input**
- [ ] Select directory with multiple curves
- [ ] Load pipeline from file
- [ ] Show file preview (list of curves to process)

#### 2. **Progress & Results**
- [ ] Live progress bar showing curves processed
- [ ] Results table: filename | E_mean | E_std | δ_max | comments
- [ ] Export results table (CSV)

#### 3. **Statistics**
- [ ] Histogram of E values across all curves
- [ ] Box plot: E distribution
- [ ] Show outliers/failed curves

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  SoftMech Batch Analyzer                                │
├─────────────────────────────────────────────────────────┤
│ [Load Pipeline] [Select Curve Dir] [Run Batch]         │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  Batch Settings      │      Results & Statistics        │
│  ────────────────    │                                  │
│  Pipeline:           │   Processing: [████████░░] 80%  │
│  pipeline_v2.json    │                                  │
│                      │   Results (Curves Processed: 5)  │
│  Input Directory:    │   ┌──────────────────────────┐  │
│  /data/afm/jan2026   │   │ File │ E(kPa) │ δ_max   │  │
│                      │   ├──────┼────────┼─────────┤  │
│  Curves Found: 12    │   │ c1   │ 4.2    │ 6.8 μm  │  │
│  [ ] Curve 1.json    │   │ c2   │ 4.5    │ 7.1 μm  │  │
│  [ ] Curve 2.json    │   │ c3   │ 4.1    │ 6.9 μm  │  │
│  [x] Curve 3.json    │   │ c4   │ ✗ fail │ n/a     │  │
│  ...                 │   │ c5   │ 4.3    │ 7.0 μm  │  │
│                      │   └──────────────────────────┘  │
│  [Process Selected]   │                                 │
│  [Process All]        │   Mean E: 4.22 ± 0.15 kPa      │
│  [Cancel]             │   Median δ: 6.9 μm             │
│                      │                                  │
│                      │   [📊 Show Statistics]          │
│                      │   [💾 Export CSV]               │
└──────────────────────┴──────────────────────────────────┘
```

### Implementation Structure

```
softmech/ui/analyzer/
├── __init__.py
├── batch_window.py         # Main batch analyzer window
├── widgets/
│   ├── __init__.py
│   ├── batch_input.py      # Input file selection
│   ├── progress_panel.py   # Progress monitoring
│   ├── results_table.py    # Results table widget
│   └── statistics_panel.py # Statistical plots
├── models/
│   ├── __init__.py
│   └── batch_processor.py  # Handles batch execution
└── dialogs/
    ├── __init__.py
    └── export_dialog.py
```

---

## Phase 3: CLI (MVP - Week 5)

### Purpose
Automate pipeline execution for integration with other tools, batch jobs, cloud services.

### MVP Features

```bash
# Basic usage
softmech-cli run pipeline.json curves/ --output results.csv

# Options
--pipeline FILE          Path to pipeline descriptor JSON
--curves FILE|DIR        Single curve or directory of curves
--output FILE            Output CSV with results
--format {json,csv,h5}   Output format
--threads N              Number of parallel threads
--verbose                Show detailed progress
```

### Implementation

```
softmech/cli/
├── __init__.py
├── main.py                # CLI entry point
├── commands/
│   ├── __init__.py
│   ├── run.py             # softmech-cli run
│   ├── validate.py        # softmech-cli validate <pipeline.json>
│   └── list_plugins.py    # softmech-cli list plugins
└── formatters/
    ├── __init__.py
    ├── csv_formatter.py
    └── json_formatter.py
```

---

## Development Roadmap

### Sprint 1 (Week 1-2): Designer UI MVP
**Goal:** Load curve, apply filter, see results

**Deliverables:**
- [ ] Main window skeleton (PySide6)
- [ ] File open dialog → load JSON curve
- [ ] Plot widget (matplotlib embedded)
- [ ] Pipeline steps panel (read-only initially)
- [ ] Single filter (savgol) with parameter controls
- [ ] Live visualization update on parameter change
- [ ] Save/load pipeline JSON

**Definition of Done:**
- User can load `tools/synth.json` curve
- Apply savgol with adjustable window_size
- See filtered curve overlay on original
- Save pipeline, reload it

### Sprint 2 (Week 3): Designer UI Complete
**Goal:** Full single-curve workflow

**Deliverables:**
- [ ] Contact point detection step
- [ ] Indentation calculation (auto)
- [ ] Elasticity spectra calculation (auto)
- [ ] Multi-tab visualization (Raw/Filtered/Indentation/Elasticity)
- [ ] Export results (CSV, PNG)
- [ ] Results metadata display

**Definition of Done:**
- User loads curve → applies filter → sees all 4 analysis results
- Can export data and plots
- Pipeline is fully serializable and reproducible

### Sprint 3 (Week 4): Batch Analyzer MVP
**Goal:** Process multiple curves

**Deliverables:**
- [ ] Directory input selector
- [ ] Batch execution engine
- [ ] Results table widget
- [ ] Basic statistics (mean, std)
- [ ] CSV export

**Definition of Done:**
- Load pipeline from Sprint 2
- Select directory with multiple curves
- Process all, show results table
- Export as CSV

### Sprint 4 (Week 5): CLI MVP
**Goal:** Command-line automation

**Deliverables:**
- [ ] Click CLI framework integration
- [ ] `softmech-cli run` command
- [ ] CSV output formatter
- [ ] Error handling and logging

**Definition of Done:**
- `softmech-cli run pipeline.json curves/ --output results.csv` works
- Produces same results as GUI batch analyzer

---

## Technology Decisions

### Why PySide6?
- ✓ Native Qt behavior on all platforms
- ✓ Handles complex UIs well
- ✓ Good for scientific/engineering apps
- ✓ Integration with matplotlib is solid

### Why magicgui?
- ✓ Auto-generate parameter widgets from type hints
- ✓ Zero UI code needed per parameter
- ✓ Plugin system already has type hints
- ✓ Fits our "zero Qt dependencies for plugins" principle

### Why Click for CLI?
- ✓ Minimal boilerplate
- ✓ Automatic help generation
- ✓ Easy subcommand structure
- ✓ Compatible with our existing codebase

---

## Key Design Principles

### 1. **Separation of Concerns**
- Core logic (plugins, pipeline) has ZERO Qt/UI dependencies ✓
- UI is purely presentation layer of validated core
- CLI reuses same UI-agnostic core

### 2. **Real-time Feedback**
- Parameters change → instant visualization update
- Live progress during batch processing
- Error messages inline, not modal dialogs

### 3. **Progressive Enhancement**
- MVP works with 1 filter (savgol)
- Additional filters added to registry → appear in UI automatically
- No UI code needs change to add new plugins

### 4. **Reproducibility**
- Every pipeline is saved as JSON
- JSON fully describes all steps + parameters
- Pipeline from Designer can run in Batch or CLI unchanged

---

## Success Metrics for Agile

- **Week 2 End:** Designer UI loads curve, applies filter, shows result (screenshot-able demo)
- **Week 4 End:** User can process 10 curves, get statistics (usable tool)
- **Week 5 End:** CLI works for automated batch processing

---

## File Structure Summary

```
softmech/
├── core/                (validated ✓)
│   ├── plugins/
│   ├── data/
│   ├── pipeline/
│   ├── algorithms/
│   └── io/
│
├── ui/                  (to be built)
│   ├── designer/
│   │   ├── main_window.py
│   │   ├── widgets/
│   │   ├── dialogs/
│   │   ├── models/
│   │   └── resources/
│   ├── analyzer/
│   │   ├── batch_window.py
│   │   ├── widgets/
│   │   └── models/
│   ├── cli/
│   │   ├── main.py
│   │   ├── commands/
│   │   └── formatters/
│   └── __init__.py
│
├── plugins/             (partially migrated)
│   ├── filters/
│   ├── contact_point/
│   ├── force_models/
│   ├── elastic_models/
│   └── exporters/
│
└── nanoindentation/     (legacy, can deprecate)
```

---

## Questions for Refinement

1. **Color scheme?** (dark/light theme preference for scientific tools?)
2. **Keyboard shortcuts?** (standard or custom?)
3. **Initial file location?** (remember last opened directory?)
4. **Export formats?** (CSV enough initially, or add others?)
5. **Real-time computation handling?** (disable UI while processing, or show spinner?)

