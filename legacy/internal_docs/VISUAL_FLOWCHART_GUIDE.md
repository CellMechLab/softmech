# Visual Pipeline Flowchart Editor - Sprint 1c Update

## New Features

### 1. **Cascading Step Boxes (Orange-Style)**
- Each pipeline step is displayed as an interactive visual box
- Boxes arranged horizontally left-to-right
- Connected with arrows showing data flow
- Clearly labeled with plugin name and step type

### 2. **Interactive Step Boxes**
- **Click** any step box to highlight it (thick orange border)
- **Double-click** or use "Edit Parameters" button to modify step parameters
- Hover effect (color change) for visual feedback

### 3. **Parameter Editing Dialog**
- Click a step box, then click "Edit Parameters"
- Dialog shows:
  - Plugin name and version
  - All available parameters for that step
  - Spinbox for integer parameters
  - Double spinbox for float parameters
  - Read-only label for other types
- Changes saved immediately to pipeline

### 4. **Control Buttons**
- **"+ Add Filter"** — Insert savgol/median/notch before contact point
- **"Remove Last Filter"** — Undo the last added filter
- **"Edit Parameters"** — Edit parameters of selected step box

### 5. **Visual Feedback**
- Step boxes change color on hover
- Selected step highlighted with thick orange border
- Info label shows total step count
- Scene auto-fits to show all steps

## Workflow

1. **Load Pipeline** → Flowchart renders with cascading boxes
2. **Click a Step** → Box highlights and becomes selected
3. **Click "Edit Parameters"** → Dialog opens showing editable parameters
4. **Modify Values** → Use spinboxes to adjust parameters
5. **Click OK** → Changes saved to pipeline, diagram refreshes
6. **Add Filter** → New box appears before contact point
7. **Run Pipeline** → All steps execute with modified parameters

## Example Pipeline Visualization

```
[Input] → [savgol] → [median] → [autothresh] → [indentation] → [elasticity_spectra]
           (filter)   (filter)   (contact_pt)    (spectral)        (spectral)
```

Each box is clickable and shows:
- Plugin name (e.g., "savgol")
- Step type (e.g., "filter")

## Testing the Visual Editor

1. Run Designer: `python softmech/ui/designer/main_window.py`
2. Create/load a pipeline
3. Left panel now shows cascading step boxes instead of text list
4. Click any box to select it
5. Click "Edit Parameters" to modify settings
6. Click "+ Add Filter" to insert new filters
7. Boxes update immediately on changes

## Known Behaviors

- Flowchart auto-scales to fit available space
- Parameters are stored in step.parameters dict
- Changes emit pipeline_changed signal
- All modifications are reversible with "Remove Last Filter"
- 1 parameter dialog open at a time (others close)

---

**Status:** Ready for testing with real pipelines and datasets.
