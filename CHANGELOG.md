# Changelog

All notable changes to the SoftMech project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-alpha] - 2026-03-08

### Major Changes
This is a complete rewrite of SoftMech with breaking changes from v0.1. The alpha release establishes the foundation for a modular, extensible AFM analysis framework.

### Added
- **Plugin Architecture** - Extensible system for filters, contact point detection, and force models
- **Visual Pipeline Designer** - Interactive UI with flowchart-based pipeline editor
- **CLI Batch Processing** - Command-line tool for high-throughput dataset analysis
- **Outlier Management** - Mark and exclude outlier curves from downstream analysis
  - Visual indication (red coloring in plots)
  - Persistent outlier flags in saved datasets
  - Automatic exclusion from fitting and averaging
- **Multi-Curve Visualization** - Interactive browsing with slider and view modes
  - Show all curves + average
  - Show average only
  - Show selected curve only
- **Results Analysis Panel** - Four-tab layout for comprehensive result exploration
  - Curves: Multi-curve viewer with contact point markers
  - Indentation: δ vs F plots
  - Elasticity: E(δ) spectra (placeholder for v2.3)
  - Results: Histogram/table/image map parameter distributions
- **Export Functionality** - Generate CSV reports with:
  - Fitting parameters from all valid curves
  - Average force-displacement curves ± std
  - Average indentation curves ± std
- **Dataset Persistence** - Save/load HDF5 and JSON with outlier annotations
- **Pipeline Files** - `.pipe` extension for pipeline descriptors

### Core Components
- `softmech.core.pipeline` - Pipeline executor and descriptor system
- `softmech.core.data` - Curve and Dataset data structures
- `softmech.core.io` - HDF5/JSON loaders and savers
- `softmech.core.plugins` - Plugin registry and discovery
- `softmech.ui.designer` - Visual pipeline designer UI
- `softmech.ui.cli` - Command-line interface

### Plugins Implemented
**Filters:**
- Savitzky-Golay smoothing
- None (pass-through)

**Contact Point Detection:**
- Auto-threshold
- Nanite integration (8 algorithms: baseline deviation, constant fit, polynomial fit, gradient zero-crossing, etc.)
- None (manual/skip)

**Force Models:**
- Hertz (spherical indenter)

### Known Limitations (To Be Addressed)
- Elasticity spectra calculation not yet implemented (planned for v2.3)
- Limited plugin selection (more filters and models in v2.1)
- No plugin creation wizard (planned for v2.2)
- No elastic model fitting yet (planned for v2.4)

### Changed
- Complete rewrite of codebase architecture
- New file formats:
  - Pipeline files now use `.pipe` extension (still JSON internally)
  - Dataset persistence includes outlier metadata
- UI paradigm shift from monolithic interface to modular designer

### Deprecated
- v0.1 interface and workflow (still available as separate release)
- Old `protocols/` plugin system (replaced by `softmech/plugins/`)

### Removed from This Release (Archived in legacy/)
- Old protocols plugin directory
- Demo and test scripts from development
- Internal sprint documentation

### Migration Notes
- v2.0 cannot directly load v0.1 project files
- Export data from v0.1 to neutral format (CSV/HDF5) for import into v2.0
- Elasticity spectra users should continue using v0.1 until v2.3 release

---

## [0.1] - 2021

### Original Release
- Monolithic GUI for AFM force curve analysis
- Fixed analysis pipeline
- Elasticity spectra calculation
- Contact point detection
- Force model fitting (Hertz variants)
- Basic visualization

**Download:** https://github.com/CellMechLab/softmech/releases/tag/v0.1

---

## Upcoming Releases

### [2.1] - Plugin Expansion (Planned)
- Additional filter plugins (notch, polynomial detrending, median)
- Extended contact point algorithms
- More force models (linear, power-law, Sneddon)
- Plugin documentation

### [2.2] - Developer Tools (Planned)
- Plugin creation wizard
- Plugin template generator
- Developer API documentation
- Example plugin packages

### [2.3] - Elasticity Spectra (Planned)
- E(δ) calculation (Hertz-based and model-fitting approaches)
- Interactive E(δ) visualization
- Quality metrics and plateau detection

### [2.4] - Advanced Analysis (Planned)
- Elastic model fitting to E(δ) spectra
- Multi-layer models (bilayer, sigmoid)
- Spatial mapping visualization
- Statistical analysis tools

---

**Note:** Development follows an iterative release model. Feedback from alpha testers will influence prioritization of upcoming features.
