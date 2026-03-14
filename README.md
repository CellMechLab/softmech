# SoftMech - AFM Analysis Pipeline

**Version:** 2.0.0-alpha  
**Status:** Alpha Release - Active Development

SoftMech is a modular, extensible pipeline framework for analyzing Atomic Force Microscopy (AFM) force curves. This complete rewrite introduces a plugin-based architecture, interactive pipeline designer, and batch processing capabilities.

> **⚠️ Alpha Release Notice**  
> This is a major rewrite with breaking changes from v0.1. The previous version remains available for users who need the legacy interface. See [Legacy Version](#legacy-version-v01) below.

---

## Features

### Core Capabilities
- **Visual Pipeline Designer** - Interactive UI for building and editing analysis workflows
- **Plugin Architecture** - Extensible system for filters, contact point detection, and force models
- **Batch Processing** - CLI tool for high-throughput analysis
- **Outlier Management** - Mark and exclude outlier curves from analysis
- **Export Results** - Generate CSV reports with fitting parameters and average curves
- **Multi-Format Support** - Load HDF5 and JSON datasets, save with outlier annotations

### Analysis Pipeline
1. **Filtering** - Savitzky-Golay smoothing, median filters, and custom preprocessing
2. **Contact Point Detection** - Multiple algorithms including auto-threshold and Nanite methods
3. **Indentation Calculation** - Cantilever compliance-corrected depth calculation
4. **Force Model Fitting** - Hertz (spherical/conical) and extensible model framework
5. **Results Visualization** - Interactive plots with histogram/table/image map views

---

## Installation

### Requirements
- Python 3.8+
- PySide6 (Qt6 for GUI)
- NumPy, SciPy, h5py
- PyQtGraph for visualization

### Setup

```bash
# Clone the repository
git clone https://github.com/CellMechLab/softmech.git
cd softmech

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### Launch the Interactive UI

**Windows:**
```bash
launch_ui.bat
```

**Linux/Mac:**
```bash
./launch_ui.sh
```

**Or directly with Python:**
```bash
python softmech_cli.py ui
```

### Basic Workflow
1. **File → Open Experiment** - Load AFM force curve dataset (HDF5 or JSON)
2. **Edit Pipeline** - Add/remove filters using the left panel flowchart editor
3. **Run Pipeline** - Click "Run Pipeline" to process all curves (by default, it runs automatically after every change)
4. **Analyze Results** - Browse curves, view indentation/elasticity, check parameter distributions
5. **Export** - File → Export Results to save CSV files with analysis data

See [DESIGNER_QUICK_START.md](DESIGNER_QUICK_START.md) and [CLI_QUICKSTART.md](CLI_QUICKSTART.md) for detailed guides.

---

## Batch Processing via CLI

Process multiple datasets with a saved pipeline:

```bash
python softmech_cli.py batch \
  --pipeline my_pipeline.pipe \
  --input ./data/curves/ \
  --output results.json
```

---

## Development Roadmap

### Completed (v2.0.0-alpha)
- ✅ Core pipeline architecture with plugin system
- ✅ Visual designer UI with flowchart editor
- ✅ Outlier marking and exclusion
- ✅ Multi-curve visualization with average curves
- ✅ Contact point detection (auto-threshold, Nanite integration)
- ✅ Hertz force model fitting
- ✅ Batch processing CLI
- ✅ HDF5/JSON dataset I/O with persistence

### Upcoming Features

#### Phase 1: Plugin Expansion (v2.1)
- Implement plugins for all existing analysis steps
- Additional filters (notch, polynomial detrending)
- More contact point algorithms (gradient-based, ROV)
- Extended force models (linear, power-law, Sneddon)

#### Phase 2: Developer Tools (v2.2)
- Plugin creation helper interface and wizard
- Plugin template generator
- Developer documentation and API reference
- Example plugin package structure

#### Phase 3: Elasticity Spectra (v2.3)
- Implement elasticity spectra calculation (E vs δ)
- Support both Hertz-based and model-fitting approaches
- Interactive E(δ) visualization in results panel
- Quality metrics (plateau detection, goodness-of-fit)

#### Phase 4: Advanced Analysis (v2.4)
- Elastic model fitting to E(δ) spectra
- Multi-layer models (bilayer, sigmoid transitions)
- Spatial mapping visualization (grid-based datasets)
- Statistical analysis tools (distribution fitting, correlations)

---

## Legacy Version (v0.1)

The original SoftMech version (v0.1) is still available for users who need the previous interface:

**Download:** [https://github.com/CellMechLab/softmech/releases/tag/v0.1](https://github.com/CellMechLab/softmech/releases/tag/v0.1)

**Key Differences:**
- v0.1: Single monolithic GUI, hardcoded pipeline, elasticity spectra included
- v2.0-alpha: Modular plugin system, customizable pipelines, no elasticity spectra yet (coming in v2.3)

**Migration Note:** v2.0 cannot directly load v0.1 project files. If migrating, export data to CSV/HDF5 from v0.1 and import into v2.0.

---

## Project Structure

```
softmech/
├── softmech/               # Core package
│   ├── core/               # Pipeline engine, data structures, I/O
│   ├── plugins/            # Plugin implementations (filters, models)
│   └── ui/                 # Designer and CLI interfaces
├── tools/                  # Helper scripts and utilities
├── legacy/                 # Archived files from v0.1 development
├── softmech_cli.py         # Main CLI entry point
├── launch_ui.*             # Platform-specific launcher scripts
└── requirements.txt        # Python dependencies
```

---

## Citation

If you use SoftMech in your research, please cite:

- **Ciccone, G., Azevedo Gonzalez Oliva, M., Antonovaite, N., Lüchtefeld, I., Salmeron-Sanchez, M. and Vassalli, M.**, 2021. Experimental and data analysis workflow for soft matter nanoindentation. *Journal of Visualized Experiments* (10.3791/63401).

- **Lüchtefeld, I., Bartolozzi, A., Mejía Morales, J., Dobre, O., Basso, M., Zambelli, T. and Vassalli, M.**, 2020. Elasticity spectra as a tool to investigate actin cortex mechanics. *Journal of Nanobiotechnology*, 18(1), pp.1-11 (doi.org/10.1186/s12951-020-00706-2).

---

## License

See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-plugin`)
3. Commit your changes with clear messages
4. Submit a pull request

For plugin development, see the upcoming Plugin Developer Guide (Phase 2).

---

## Support

- **Issues:** [GitHub Issues](https://github.com/CellMechLab/softmech/issues)
- **Documentation:** See `CLI_QUICKSTART.md` and `DESIGNER_QUICK_START.md`
- **Legacy Docs:** Check `legacy/internal_docs/` for development history

---

**Last Updated:** March 8, 2026

