#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SoftMech - AFM Analysis Pipeline CLI and UI Launcher

Dual-purpose entry point:
- Launch interactive UI: softmech_cli ui
- Batch process data: softmech_cli batch --pipeline <file> --input <dir> --output <file>
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import click
import numpy as np

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from softmech.core.data import Dataset, Curve
from softmech.core.io import loaders
from softmech.core.plugins import PluginRegistry
from softmech.core.pipeline import PipelineDescriptor, PipelineExecutor

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """SoftMech AFM Analysis Pipeline Tool
    
    Use 'softmech_cli ui' to launch the interactive UI
    Use 'softmech_cli batch' for command-line batch processing
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Store verbose flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.pass_context
def ui(ctx: click.Context) -> None:
    """Launch the interactive SoftMech UI
    
    Example:
        softmech_cli ui
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        click.echo("Launching SoftMech Designer UI...")
        _launch_designer_ui()
    except Exception as e:
        click.echo(f"Error launching UI: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _launch_designer_ui() -> None:
    """Launch the SoftMech Designer UI."""
    from PySide6.QtWidgets import QApplication
    from softmech.ui.designer.main_window import DesignerMainWindow
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = DesignerMainWindow()
    window.show()
    sys.exit(app.exec())


@cli.command()
@click.option(
    '--pipeline',
    type=click.Path(exists=True),
    required=True,
    help='Path to pipeline descriptor JSON file'
)
@click.option(
    '--input',
    'input_dir',
    type=click.Path(exists=True),
    required=True,
    help='Directory containing input files (HDF5, CSV, etc.)'
)
@click.option(
    '--output',
    'output_file',
    type=click.Path(),
    required=True,
    help='Output file for fit parameters (JSON or HDF5)'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['json', 'hdf5'], case_sensitive=False),
    default='json',
    help='Output format for results'
)
@click.option(
    '--pattern',
    type=str,
    default='*.h5',
    help='File pattern to match in input directory (default: *.h5)'
)
@click.option(
    '--progress',
    is_flag=True,
    help='Show progress bar during processing'
)
@click.pass_context
def batch(
    ctx: click.Context,
    pipeline: str,
    input_dir: str,
    output_file: str,
    output_format: str,
    pattern: str,
    progress: bool
) -> None:
    """Batch process AFM curves through a pipeline
    
    Example:
        softmech_cli batch \\
            --pipeline my_pipeline.json \\
            --input ./data \\
            --output ./results.json
    
    Or with HDF5 output:
        softmech_cli batch \\
            --pipeline my_pipeline.json \\
            --input ./data \\
            --output ./results.h5 \\
            --format hdf5
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Load pipeline descriptor
        click.echo(f"Loading pipeline: {pipeline}")
        with open(pipeline, 'r') as f:
            pipeline_data = json.load(f)
        pipeline_desc = PipelineDescriptor.from_dict(pipeline_data)
        
        # Find input files
        input_path = Path(input_dir)
        input_files = list(input_path.glob(pattern))
        
        if not input_files:
            click.echo(
                f"No files matching pattern '{pattern}' found in {input_dir}",
                err=True
            )
            sys.exit(1)
        
        click.echo(f"Found {len(input_files)} input files")
        
        # Initialize executor and registry
        registry = PluginRegistry()
        executor = PipelineExecutor(registry)
        
        # Process each file
        results = []
        
        # Setup progress bar if requested
        iterator = (
            click.progressbar(
                input_files,
                label='Processing curves',
                show_pos=True
            ) if progress else input_files
        )
        
        with iterator if progress else _null_context(iterator):
            for input_file in iterator:
                try:
                    click.echo(f"Processing: {input_file.name}")
                    
                    # Load dataset
                    dataset = loaders.load_dataset_from_file(str(input_file))
                    
                    # Execute pipeline
                    processed_dataset = executor.execute(
                        pipeline_desc,
                        dataset,
                        progress_callback=None
                    )
                    
                    # Extract fit parameters from results
                    file_results = _extract_fit_parameters(
                        input_file.name,
                        processed_dataset
                    )
                    results.extend(file_results)
                    
                except Exception as e:
                    error_msg = f"Error processing {input_file.name}: {e}"
                    click.echo(error_msg, err=True)
                    if verbose:
                        import traceback
                        traceback.print_exc()
                    results.append({
                        'file': input_file.name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        # Save results
        click.echo(f"Saving results to: {output_file}")
        _save_results(results, output_file, output_format)
        
        click.echo(f"✓ Batch processing complete ({len(results)} curves processed)")
        
    except Exception as e:
        click.echo(f"Batch processing failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _extract_fit_parameters(filename: str, dataset: Dataset) -> List[Dict[str, Any]]:
    """
    Extract fit parameters from processed dataset.
    
    This function extracts the results stored in each curve's processing_result
    and organizes them by step. Currently supports extracting:
    - Force model fit parameters (slope, radius, etc.)
    - Elasticity model parameters
    - Quality metrics (R², residuals)
    
    Parameters
    ----------
    filename : str
        Name of the source file
    dataset : Dataset
        Processed dataset
    
    Returns
    -------
    List[Dict[str, Any]]
        List of result dictionaries, one per curve
    """
    results = []
    
    for curve_idx, curve in enumerate(dataset.curves):
        result = {
            'file': filename,
            'curve_index': curve_idx,
            'status': 'success',
            'fit_parameters': {}
        }
        
        # Extract data from curve's processing result if available
        if hasattr(curve, 'processing_result') and curve.processing_result:
            proc_result = curve.processing_result
            
            # Store all step results with their parameter data
            if hasattr(proc_result, 'step_results') and proc_result.step_results:
                for step_name, step_data in proc_result.step_results.items():
                    if isinstance(step_data, dict):
                        result['fit_parameters'][step_name] = step_data
        
        results.append(result)
    
    return results


def _save_results(
    results: List[Dict[str, Any]],
    output_file: str,
    format_type: str
) -> None:
    """
    Save batch processing results to file.
    
    Parameters
    ----------
    results : List[Dict]
        Processing results
    output_file : str
        Output file path
    format_type : str
        Output format ('json' or 'hdf5')
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format_type.lower() == 'json':
        # Convert numpy types to JSON-serializable types
        json_results = _make_json_serializable(results)
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
    
    elif format_type.lower() == 'hdf5':
        import h5py
        with h5py.File(output_file, 'w') as f:
            _save_results_hdf5(f, results)
    
    else:
        raise ValueError(f"Unknown output format: {format_type}")


def _make_json_serializable(obj: Any) -> Any:
    """Convert numpy and other non-serializable types to JSON-compatible types."""
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def _save_results_hdf5(h5_file: 'h5py.File', results: List[Dict[str, Any]]) -> None:
    """Save results to HDF5 file."""
    for idx, result in enumerate(results):
        group = h5_file.create_group(f"curve_{idx:04d}")
        
        # Store metadata
        for key in ['file', 'curve_index', 'status']:
            if key in result:
                group.attrs[key] = str(result[key])
        
        # Store fit parameters
        if 'fit_parameters' in result and result['fit_parameters']:
            params_group = group.create_group('fit_parameters')
            for step_name, params in result['fit_parameters'].items():
                if isinstance(params, dict):
                    step_group = params_group.create_group(step_name)
                    for param_name, param_value in params.items():
                        try:
                            if isinstance(param_value, (int, float, str, bool)):
                                step_group.attrs[param_name] = param_value
                            elif isinstance(param_value, (list, np.ndarray)):
                                step_group.create_dataset(param_name, data=param_value)
                        except (TypeError, ValueError):
                            # Skip parameters that can't be stored
                            pass


class _NullContext:
    """Context manager that does nothing."""
    def __init__(self, iterable):
        self.iterable = iterable
    
    def __enter__(self):
        return self.iterable
    
    def __exit__(self, *args):
        pass


def _null_context(iterable):
    """Return a no-op context manager for the iterable."""
    return _NullContext(iterable)


if __name__ == '__main__':
    # If no arguments provided, launch UI by default
    if len(sys.argv) == 1:
        sys.argv.append('ui')
    
    cli(obj={})
