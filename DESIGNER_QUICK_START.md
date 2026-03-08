# SoftMech Designer UI - Quick Start Guide

## Launching the Designer

```bash
cd c:\Users\mv68b\git\softmech
python softmech/ui/designer/main_window.py
```

The window will open with:
- **Left Panel:** Pipeline flowchart editor
- **Right Panel:** 4-tab visualization suite

## Main Workflow

### Step 1: Load Data
1. Menu: **File → Open Curve**
2. Select a JSON or HDF5 file containing AFM force curves
3. **Tab 1 (Curves)** shows all curves + average curve
4. Use slider/spinbox to browse individual curves

### Step 2: Edit Pipeline (Optional)
Default pipeline: Savgol → Auto Threshold → Indentation → Elasticity

To add filters:
1. Click **"+ Add Filter"** button in left panel
2. Select filter (Savgol, Median, Notch)
3. Filter inserts before Contact Point detection

To remove filters:
- Click **"Remove Last Filter"** button

Current pipeline steps shown as text list below flowchart canvas.

### Step 3: Run Pipeline
1. Click **"Run Pipeline"** button on left
2. Progress dialog shows real-time execution
3. All curves processed sequentially
4. Cancel anytime with dialog button

### Step 4: Analyze Results

#### Tab 1: Curves
- Browse all curves with interactive slider
- A lightweight dropdown selects view mode:
  - **Show All** — overlay all + average
  - **Show Average Only** — dataset mean curve
  - **Show Selected Only** — single curve
- Red circles mark contact points

#### Tab 2: Indentation
- Shows indentation depth (δ) vs force for selected curve
- Updates automatically when you change curves in Tab 1
- Displays "No indentation data" until CP detection runs

#### Tab 3: Elasticity
- Shows Young's modulus E(δ) on log-log axis
- Updates automatically for selected curve
- Displays "No elasticity data" until spectra calculation runs

#### Tab 4: Results
A suite for analyzing parameter distributions:

**Select parameter:**
- Young's Modulus (E) — average E from elasticity spectra
- Contact Point (Z_cp) — Z displacement where contact detected
- Force at Contact (F_cp) — force value at contact
- Fit Residuals (R²) — model fit quality

**Select view:**
- **Histogram** — binned distribution across dataset
- **Table** — scatter plot (index vs value)
- **Image Map** — 2D spatial map (if dataset is N×N square)

Example: Load 25-curve dataset → Tab 4 → Histogram of E shows modulus distribution; Switch to Image Map → see E variation as 5×5 grid.

### Step 5: Export

**Export Data (CSV)**
- Saves Z, F, δ, force_indentation, δ_e, E columns
- Tab-separated for spreadsheet import

**Export Plot (PNG)**
- Saves active tab as high-resolution image
- Useful for presentations/reports

## Tips & Tricks

- **Synced Controls:** Slider and spinbox in Tab 1 are linked — change one, other updates
- **Real-time Updates:** After running pipeline, switching curves automatically refreshes indentation & elasticity tabs
- **Pipeline Persistence:** Save/load pipelines via File menu (JSON format)
- **Batch Processing:** Load single file, run pipeline once, then browse all results in Tab 1

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Curve | `Ctrl+O` |
| Save Pipeline | `Ctrl+S` |
| Load Pipeline | `Ctrl+L` |
| Exit | `Ctrl+Q` |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No dataset loaded" error | Use File → Open Curve first |
| Indentation tab empty after run | Ensure autothresh contact point ran (normally first in pipeline) |
| Elasticity tab empty | Indentation must be calculated first (CP must exist) |
| Results histogram shows wrong parameter | Check Parameter dropdown in Tab 4 |
| Image Map doesn't display | Dataset must be perfect square (4, 9, 16, 25, 36, etc. curves) |

## File Format Requirements

### JSON Format
```json
{
  "curves": [
    {
      "data": {"Z": [...], "F": [...]},
      "spring_constant": 0.032,
      "tip": {"geometry": "sphere", "radius": 1e-6}
    },
    ...
  ]
}
```

### HDF5 Format
- Groups per curve with datasets: `Z`, `F`
- Attributes: `spring_constant`, `tip_geometry`

## Performance Notes

- **Large Datasets:** 100+ curves may take minutes to process
  - Progress dialog shows real-time step names & curve count
  - Cancel anytime if needed
- **UI Responsiveness:** Visualization updates happen after entire pipeline completes
  - Multi-curve view is fast (interpolated average)
  - Results histogram computed on-demand when Tab 4 selected

## Next Steps

After mastering the Designer:
1. **Save pipelines** (File → Save Pipeline) for reuse
2. **Batch process** multiple datasets with same pipeline
3. **Tune parameters** via properties panel (coming Sprint 2)
4. **Export results** to Excel/Matlab for further analysis

---

**Questions?** Check [SPRINT_1C_COMPLETION.md](SPRINT_1C_COMPLETION.md) for architecture details.
