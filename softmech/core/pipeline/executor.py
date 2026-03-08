"""
Pipeline executor - runs a PipelineDescriptor on datasets.
"""

from typing import Callable, Optional, Dict, Any, List
import logging
import traceback

from softmech.core.data import Curve, Dataset, ProcessingResult
from softmech.core.plugins import PluginRegistry
from softmech.core.pipeline.descriptor import PipelineDescriptor, PipelineStep
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context for pipeline execution - tracks state and progress."""

    def __init__(self, dataset: Dataset):
        """
        Initialize execution context.

        Parameters
        ----------
        dataset : Dataset
            Dataset to process
        """
        self.dataset = dataset
        self.current_curve_index = 0
        self.current_step_index = 0
        self.total_steps = 0
        self.errors: List[str] = []
        self.registry = PluginRegistry()

    def add_error(self, message: str) -> None:
        """Log an error during execution."""
        self.errors.append(message)
        logger.error(message)


class PipelineExecutor:
    """
    Executes a pipeline on a dataset.

    Applies all steps in sequence to all curves, with optional progress monitoring.
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        Initialize executor.

        Parameters
        ----------
        registry : PluginRegistry, optional
            Plugin registry. If None, a new one is created.
        """
        self.registry = registry or PluginRegistry()

    def execute(
        self,
        descriptor: PipelineDescriptor,
        dataset: Dataset,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dataset:
        """
        Execute a pipeline on a dataset.

        Parameters
        ----------
        descriptor : PipelineDescriptor
            Pipeline to execute
        dataset : Dataset
            Dataset to process
        progress_callback : callable, optional
            Callback function(message: str, progress: float) for monitoring

        Returns
        -------
        Dataset
            Processed dataset (same object, modified in place)

        Raises
        ------
        RuntimeError
            If critical errors occur during execution
        """
        context = ExecutionContext(dataset)
        steps = descriptor.get_all_steps()
        context.total_steps = len(steps)

        if not steps:
            logger.warning("Pipeline has no steps")
            return dataset

        try:
            # Execute each step on all curves
            for step_idx, step in enumerate(steps):
                context.current_step_index = step_idx
                self._execute_step(step, context, progress_callback)

                if progress_callback:
                    progress = (step_idx + 1) / context.total_steps
                    progress_callback(f"Completed step: {step.plugin_id}", progress)

        except Exception as e:
            error_msg = f"Fatal pipeline error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            context.add_error(error_msg)
            raise RuntimeError(error_msg) from e

        if context.errors:
            logger.warning(f"Pipeline completed with {len(context.errors)} errors")

        return dataset

    def _execute_step(
        self,
        step: PipelineStep,
        context: ExecutionContext,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        Execute a single pipeline step on all curves.

        Parameters
        ----------
        step : PipelineStep
            Step to execute
        context : ExecutionContext
            Execution context
        progress_callback : callable, optional
            Progress callback
        """
        logger.info(f"Executing step: {step.type} / {step.plugin_id}")

        # Skip "none" placeholder steps
        if step.plugin_id == "none":
            logger.info(f"Skipping step {step.type} with plugin_id='none'")
            return

        # Special handling for certain step types
        if step.type in ("indentation", "elasticity_spectra"):
            self._execute_spectral_step(step, context, progress_callback)
            return

        # Standard plugin execution
        try:
            plugin = self.registry.get(step.plugin_id)
        except KeyError:
            msg = f"Plugin not found: {step.plugin_id}"
            context.add_error(msg)
            return

        # Set parameters from descriptor
        try:
            plugin.set_parameters_dict(step.parameters)
        except Exception as e:
            msg = f"Error setting parameters for {step.plugin_id}: {e}"
            context.add_error(msg)
            return

        # Execute on each curve
        for curve_idx, curve in enumerate(context.dataset):
            context.current_curve_index = curve_idx

            # Skip outliers only for elasticity-related downstream analysis.
            # Keep indentation + force_model for outliers so fitted parameters
            # remain available for diagnostic plotting (red dots).
            if step.type in ("elasticity_spectra", "elastic_model") and curve.is_outlier:
                logger.info(f"Skipping outlier curve {curve_idx} for {step.type} step")
                continue

            try:
                # Select input data based on step type
                if step.type == "force_model":
                    x, y = curve.get_indentation_data()
                    if x is None or y is None or len(x) == 0:
                        logger.warning(
                            f"No indentation data for force model on curve {curve_idx}; skipping"
                        )
                        continue
                elif step.type == "elastic_model":
                    x, y = curve.get_elasticity_spectra()
                    if x is None or y is None or len(x) == 0:
                        logger.warning(
                            f"No elasticity spectra data for elastic model on curve {curve_idx}; skipping"
                        )
                        continue
                else:
                    x, y = curve.get_current_data()

                # Run plugin
                result = plugin.calculate(x, y, curve=curve)

                if result is None or result is False:
                    logger.warning(f"Plugin {step.plugin_id} failed on curve {curve_idx}")
                    continue

                # Handle result based on step type
                if step.type == "filter":
                    x_filt, y_filt = result
                    curve.set_filtered_data(x_filt, y_filt)

                elif step.type == "contact_point":
                    z_cp, f_cp = result
                    curve.set_contact_point(z_cp, f_cp)
                    
                    # Auto-calculate indentation after CP
                    from softmech.core.algorithms import spectral
                    try:
                        spectral.calculate_indentation(curve, zero_force=True)
                    except Exception as e:
                        logger.warning(f"Auto-calculation after CP failed for curve {curve_idx}: {e}")

                elif step.type == "force_model":
                    curve.set_force_model_params(result)

                elif step.type == "elastic_model":
                    curve.set_elastic_model_params(result)

                # Record in processing history
                proc_result = ProcessingResult(
                    step_name=step.type,
                    plugin_id=step.plugin_id,
                    plugin_version=step.plugin_version,
                    parameters=step.parameters,
                    timestamp=datetime.now(),
                )
                curve.record_processing_step(proc_result)

            except Exception as e:
                msg = f"Error processing curve {curve_idx} with {step.plugin_id}: {e}"
                context.add_error(msg)
                logger.error(msg)
                logger.debug(traceback.format_exc())
                # For filters, log the actual data issue
                if step.type == "filter":
                    logger.error(f"Filter {step.plugin_id} failed - input: Z({len(x)} pts), F({len(y)} pts)")
                    logger.error(f"Step parameters: {step.parameters}")

            if progress_callback and len(context.dataset) > 0:
                step_progress = (context.current_step_index + 1) / context.total_steps
                curve_progress = curve_idx / len(context.dataset)
                total_progress = (
                    step_progress * 0.9 + curve_progress * 0.1
                )  # Weight: 90% steps, 10% curves
                progress_callback(
                    f"{step.plugin_id}: curve {curve_idx + 1}/{len(context.dataset)}",
                    total_progress,
                )

    def _execute_spectral_step(
        self,
        step: PipelineStep,
        context: ExecutionContext,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        Execute spectral analysis steps (indentation, elasticity).

        These are computed from the contact point and don't use plugins.

        Parameters
        ----------
        step : PipelineStep
            Step descriptor
        context : ExecutionContext
            Execution context
        progress_callback : callable, optional
            Progress callback
        """
        from softmech.core.algorithms import spectral

        for curve_idx, curve in enumerate(context.dataset):
            context.current_curve_index = curve_idx

            # Skip outliers only for elasticity_spectra; keep indentation for
            # outliers so force-model fitting can still run for diagnostics.
            if curve.is_outlier and step.type == "elasticity_spectra":
                logger.info(f"Skipping outlier curve {curve_idx} for {step.type} step")
                if progress_callback and len(context.dataset) > 0:
                    curve_progress = (curve_idx + 1) / len(context.dataset)
                    progress_callback(f"{step.type}: curve {curve_idx + 1} (skipped - outlier)", curve_progress)
                continue

            try:
                if step.type == "indentation":
                    spectral.calculate_indentation(
                        curve,
                        zero_force=step.parameters.get("zero_force", True),
                    )

                elif step.type == "elasticity_spectra":
                    spectral.calculate_elasticity_spectra(
                        curve,
                        window_size=step.parameters.get("window_size", 5),
                        order=step.parameters.get("order", 3),
                        interpolate=step.parameters.get("interpolate", True),
                    )

                # Record in history
                proc_result = ProcessingResult(
                    step_name=step.type,
                    plugin_id=step.type,
                    plugin_version="1.0.0",
                    parameters=step.parameters,
                    timestamp=datetime.now(),
                )
                curve.record_processing_step(proc_result)

            except Exception as e:
                msg = f"Error in {step.type} for curve {curve_idx}: {e}"
                context.add_error(msg)
                logger.error(msg)

            if progress_callback and len(context.dataset) > 0:
                curve_progress = (curve_idx + 1) / len(context.dataset)
                progress_callback(f"{step.type}: curve {curve_idx + 1}", curve_progress)
