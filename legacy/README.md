# Legacy Files - SoftMech v0.1 Development Archive

This directory contains files from the original SoftMech v0.1 and early v2.0 development that have been archived during the alpha release cleanup.

## Contents

### `protocols/`
**Old plugin system** - First iteration of the plugin architecture, replaced by `softmech/plugins/` in v2.0.

Contains:
- `cpoint/` - Contact point detection algorithms
- `emodels/` - Elastic models (bilayer, sigmoid, constant)
- `exporters/` - Data export plugins
- `filters/` - Preprocessing filters
- `fmodels/` - Force models (Hertz variants)

**Status:** Superseded by the refactored plugin system in `softmech/plugins/`. May be useful for:
- Reference implementations when developing v2.0 plugins
- Elasticity spectra model implementations (to be reintegrated in v2.3)
- Historical context for design decisions

### `demo_scripts/`
**Development and testing scripts** used during v2.0 implementation:

- `debug_elasticity.py` - Elasticity calculation debugging
- `demo_*.py` - Feature demonstrations and workflow examples
- `test_*.py` - Integration and validation tests
- `PIPELINE_BUILDER_DESIGN.py` - Early pipeline builder prototype
- `PLOTTING_COMPARISON.py` - Visualization system comparison

**Status:** Not part of the alpha release. Useful for:
- Understanding design iterations
- Testing examples for future development
- Debugging reference

### `internal_docs/`
**Development documentation** from v2.0 implementation sprints:

- `SPRINT*.md` - Sprint completion reports and feature summaries
- `FITTING_REGION_FEATURE.md` - Fitting region implementation notes
- `FORCE_MODEL_INTEGRATION.md` - Force model integration design
- `NANITE_PIPELINE_ANALYSIS.md` - Nanite library integration analysis
- `PIPELINE_ARCHITECTURE.md` - Pipeline system architecture documentation
- `PLUGIN_ABOUT_DIALOG.md` - Plugin info dialog design
- `UI_ARCHITECTURE.md` - UI component structure
- `VISUAL_FLOWCHART_GUIDE.md` - Flowchart editor design guide

**Status:** Archived internal documentation. Useful for:
- Understanding v2.0 design decisions
- Reviewing feature implementation details
- Developer onboarding context

## Using Legacy Content

### Reintegrating Features
When implementing elasticity spectra (roadmap v2.3), refer to:
- `protocols/emodels/` - Elastic model implementations
- `protocols/exporters/` - Export plugin patterns
- `internal_docs/FORCE_MODEL_INTEGRATION.md` - Integration approach

### Plugin Development
When creating new plugins (roadmap v2.1-v2.2), reference:
- `protocols/filters/` - Filter plugin examples
- `protocols/cpoint/` - Contact point algorithm patterns
- Plugin skeleton files (`_skeleton.py`)

### Historical Context
Sprint reports provide chronological development history:
- Sprint 1: Core pipeline architecture
- Sprint 1c: UI enhancement and multi-curve visualization
- Outlier feature: Data quality management implementation

## Migration from v0.1

The `protocols/` folder was the primary analysis engine in v0.1. Key differences in v2.0:

| v0.1 (protocols/)           | v2.0 (softmech/plugins/)        |
|-----------------------------|----------------------------------|
| Manual plugin registration  | Automatic plugin discovery       |
| JSON-based configuration    | `.pipe` file format              |
| No UI pipeline editor       | Visual flowchart designer        |
| Elasticity spectra included | Not yet implemented (v2.3)       |
| Fixed analysis workflow     | Customizable pipeline steps      |

---

**Note:** Files in this directory are not loaded by the active v2.0 codebase and can be safely ignored by end users. Developers may find them useful for reference during plugin development and feature implementation.

**Last Updated:** March 8, 2026
