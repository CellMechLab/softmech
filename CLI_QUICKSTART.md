# SoftMech CLI - Startup Guide

## Quick Start

> ⚠️ Experimental: The command-line interface is still evolving in the alpha series.
> Command names, options, and pipeline behavior may change between releases.

### Launching the UI (Default)

The easiest way to get started is to use one of the launcher scripts or run the script directly:

**Windows (Command Prompt):**
```bash
launch_ui.bat
```

**Windows (PowerShell):**
```powershell
.\launch_ui.ps1
```

**Linux/macOS:**
```bash
./launch_ui.sh
```

**Or run the script directly (launches UI by default):**
```bash
python softmech_cli.py
```

These scripts automatically activate your virtual environment and launch the SoftMech Designer UI.

### Command-Line Interface

For advanced users and batch processing, use the `softmech_cli.py` script directly:

```bash
python softmech_cli.py --help
```

## Usage Modes

### Interactive UI

Launch the SoftMech Designer for interactive pipeline design and analysis:

```bash
python softmech_cli.py ui
# Or simply (since UI is the default):
python softmech_cli.py
```

**Examples:**
```bash
# Launch the Designer UI explicitly
python softmech_cli.py ui

# Or just run without arguments (UI is the default)
python softmech_cli.py
```

### 2. Batch Processing

Process multiple AFM curves through a pipeline and save fit parameters:

```bash
python softmech_cli.py batch \
  --pipeline <pipeline.pipe> \
    --input <input_directory> \
    --output <output_file> \
    [options]
```

**Required Options:**
- `--pipeline PATH`: Path to pipeline descriptor `.pipe` file (JSON content)
- `--input PATH`: Directory containing input files
- `--output PATH`: Output file for results

**Optional Options:**
- `--format {json|hdf5}`: Output format (default: json)
- `--pattern PATTERN`: File glob pattern to match (default: *.h5)
- `--progress`: Show progress bar during processing

**Examples:**

```bash
# Basic batch processing with JSON output
python softmech_cli.py batch \
  --pipeline my_pipeline.pipe \
    --input ./data \
    --output ./results.json

# Process with HDF5 output and progress bar
python softmech_cli.py batch \
  --pipeline pipelines/standard.pipe \
    --input ./experimental_data \
    --output ./results.h5 \
    --format hdf5 \
    --progress

# Process only CSV files with custom pattern
python softmech_cli.py batch \
  --pipeline my_pipeline.pipe \
    --input ./data \
    --output ./results.json \
    --pattern "*.csv"
```

## Pipeline Descriptor Format

Create a `pipeline.pipe` file to define your analysis pipeline (JSON syntax). Example:

```json
{
  "metadata": {
    "name": "Standard AFM Analysis",
    "description": "Typical filtering, contact point detection, and Hertz fitting"
  },
  "stages": [
    {
      "type": "FilteringStage",
      "steps": [
        {
          "name": "filter1",
          "type": "savgol",
          "parameters": {
            "window_size": 25,
            "order": 3
          }
        }
      ]
    },
    {
      "type": "ContactPointStage",
      "steps": [
        {
          "name": "contact",
          "type": "autothresh",
          "parameters": {
            "threshold": 0.5
          }
        }
      ]
    },
    {
      "type": "ForceModelStage",
      "steps": [
        {
          "name": "force_fit",
          "type": "hertz",
          "parameters": {
            "radius": 3.4e-6
          }
        }
      ]
    }
  ]
}
```

See `PIPELINE_ARCHITECTURE.md` for detailed pipeline structure documentation.

## Output Results Format

### JSON Output

Results are saved as a JSON array with processing results for each curve:

```json
[
  {
    "file": "sample_001.h5",
    "curve_index": 0,
    "status": "success",
    "fit_parameters": {
      "force_fit": {
        "parameters": {
          "radius": 3.4e-6,
          "Young_modulus": 1.2e9
        },
        "r_squared": 0.987,
        "residuals": [array of residual values]
      }
    }
  }
]
```

### HDF5 Output

Results are organized hierarchically:

```
results.h5
├── curve_0000/
│   ├── attributes: file, curve_index, status
│   └── fit_parameters/
│       └── force_fit/
│           ├── attributes: radius, Young_modulus
│           └── datasets: residuals, ...
├── curve_0001/
│   ...
```

## Global Options

All commands support `--verbose` for detailed logging:

```bash
python softmech_cli.py --verbose batch --pipeline ... --input ... --output ...
python softmech_cli.py --verbose ui
```

## Troubleshooting

### Virtual Environment Not Found

If you see warnings about the virtual environment:

1. Create a virtual environment if not already present:
   ```bash
   python -m venv .venv
   ```

2. Install dependencies:
   ```bash
   .venv\Scripts\pip install -r requirements.txt  # Windows
   source .venv/bin/pip install -r requirements.txt  # Linux/macOS
   ```

3. Manually activate before running:
   ```bash
   .venv\Scripts\activate.bat  # Windows
   source .venv/bin/activate   # Linux/macOS
   ```

### Import Errors

Ensure the project root is set correctly. The CLI script automatically handles this, but if you're running the script from a different directory:

```bash
cd /path/to/softmech
python softmech_cli.py [command]
```

### Pipeline Not Loading

Verify your pipeline descriptor:
```bash
python softmech_cli.py --verbose batch --pipeline my_pipeline.pipe ...
```

The verbose flag will show detailed error messages during pipeline loading.

## Advanced Usage

### Creating Custom Pipelines Programmatically

You can also create and execute pipelines directly in Python:

```python
from softmech.core.pipeline import PipelineDescriptor, PipelineExecutor
from softmech.core.io import loaders
import json

# Load pipeline
with open('my_pipeline.pipe') as f:
    pipeline_data = json.load(f)
pipeline = PipelineDescriptor.from_dict(pipeline_data)

# Load dataset
dataset = loaders.load_dataset_from_file('sample.h5')

# Execute
executor = PipelineExecutor()
results = executor.execute(pipeline, dataset)
```

## File Structure

```
softmech/
├── softmech_cli.py           # Main CLI entry point (this file)
├── launch_ui.bat             # Windows batch launcher
├── launch_ui.ps1             # Windows PowerShell launcher
├── launch_ui.sh              # Linux/macOS bash launcher
├── PIPELINE_ARCHITECTURE.md  # Pipeline specification
├── nano.py                   # Legacy UI implementation
└── softmech/
    ├── core/
    │   ├── data/            # Data structures
    │   ├── io/              # File loaders
    │   ├── pipeline/        # Pipeline engine
    │   └── plugins/         # Plugin system
    └── ui/
        ├── designer/        # New Designer UI
        └── cli/             # CLI commands
```

## Future Extensions

The batch processing framework is designed to be extended. You can:

1. Add new output formats by extending `_save_results()`
2. Add new input file types via the loaders module
3. Implement custom result extraction in `_extract_fit_parameters()`
4. Add new CLI commands under the `@cli` group

Example: Adding a new output format:

```python
@cli.command()
def export_results():
    """Export results to a different format"""
    # Your custom export logic here
    pass
```
