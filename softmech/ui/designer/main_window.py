"""
SoftMech Designer - Interactive AFM Analysis Pipeline Builder

Main application window for designing and testing analysis pipelines.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSplitter, QLabel, QFileDialog, QStatusBar, QMessageBox, QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QAction, QCursor

import numpy as np

# Core imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from softmech.core.data import Dataset, Curve
from softmech.core.io import loaders
from softmech.core.plugins import PluginRegistry
from softmech.core.pipeline import PipelineDescriptor, PipelineMetadata, PipelineStage, PipelineStep, PipelineExecutor
from softmech.ui.designer.widgets import (
    PipelineEditorWidget, VisualizationWidget, 
    FlowchartPipelineEditorWidget, EnhancedVisualizationWidget,
    BlockBasedPipelineEditor
)

logger = logging.getLogger(__name__)


class DesignerMainWindow(QMainWindow):
    """Main window for SoftMech Designer UI."""

    def __init__(self):
        """Initialize the Designer UI."""
        super().__init__()
        
        self.setWindowTitle("SoftMech Designer - AFM Analysis Pipeline Builder")
        self.setGeometry(100, 100, 1400, 900)
        
        # Core data
        self.current_curve: Optional[Curve] = None
        self.current_dataset: Optional[Dataset] = None
        self.pipeline: Optional[PipelineDescriptor] = None
        self.plugin_registry: PluginRegistry = PluginRegistry()
        self.current_pipeline_file: Optional[Path] = None
        self.pipeline_editor: Optional[BlockBasedPipelineEditor] = None
        self.visualization_widget: Optional[VisualizationWidget] = None
        
        # Initialize plugin registry with builtin plugins
        self._init_plugin_registry()
        
        # Setup UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()

        self._ensure_pipeline()
        
        logger.info("SoftMech Designer initialized")

    def _init_plugin_registry(self) -> None:
        """Discover and load plugins from softmech/plugins directory."""
        plugins_path = Path(__file__).parent.parent.parent / "plugins"
        
        if plugins_path.exists():
            try:
                self.plugin_registry.discover(
                    plugins_path / "filters",
                    "softmech.plugins.filters",
                    "filter"
                )
                logger.info(f"Discovered filters: {self.plugin_registry.list('filter')}")
                
                self.plugin_registry.discover(
                    plugins_path / "contact_point",
                    "softmech.plugins.contact_point",
                    "contact_point"
                )
                logger.info(f"Discovered contact point detectors: {self.plugin_registry.list('contact_point')}")

                self.plugin_registry.discover(
                    plugins_path / "force_models",
                    "softmech.plugins.force_models",
                    "force_model"
                )
                logger.info(f"Discovered force models: {self.plugin_registry.list('force_model')}")
            except Exception as e:
                logger.warning(f"Failed to discover plugins: {e}")

    def _setup_menu_bar(self) -> None:
        """Setup application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Experiment", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_curve)
        file_menu.addAction(open_action)

        info_action = QAction("Experiment &Info", self)
        info_action.setShortcut("Ctrl+I")
        info_action.triggered.connect(self.show_experiment_info)
        file_menu.addAction(info_action)
        
        save_dataset_action = QAction("Save &Dataset", self)
        save_dataset_action.setShortcut("Ctrl+D")
        save_dataset_action.setToolTip("Save dataset with outlier flags for reproducibility")
        save_dataset_action.triggered.connect(self.save_dataset)
        file_menu.addAction(save_dataset_action)
        
        file_menu.addSeparator()
        
        save_pipeline_action = QAction("&Save Pipeline", self)
        save_pipeline_action.setShortcut("Ctrl+S")
        save_pipeline_action.triggered.connect(self.save_pipeline)
        file_menu.addAction(save_pipeline_action)
        
        load_pipeline_action = QAction("&Load Pipeline", self)
        load_pipeline_action.setShortcut("Ctrl+L")
        load_pipeline_action.triggered.connect(self.load_pipeline)
        file_menu.addAction(load_pipeline_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_central_widget(self) -> None:
        """Setup main content area with splitter."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Pipeline editor
        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)
        
        # Right panel: Visualization
        right_widget = self._create_right_panel()
        splitter.addWidget(right_widget)
        
        # Set initial sizes (30% left, 70% right)
        splitter.setSizes([400, 1000])
        
        layout.addWidget(splitter)

    def _create_left_panel(self) -> QWidget:
        """Create left panel with block-based pipeline editor."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.pipeline_editor = BlockBasedPipelineEditor(self.plugin_registry)
        self.pipeline_editor.pipeline_changed.connect(self._on_pipeline_changed)
        layout.addWidget(self.pipeline_editor)

        # Real-time update toggle
        from PySide6.QtWidgets import QCheckBox
        self.realtime_cb = QCheckBox("Real-time Update")
        self.realtime_cb.setToolTip("Auto-update visualization when pipeline changes")
        self.realtime_cb.setChecked(True)
        layout.addWidget(self.realtime_cb)
        
        # Run pipeline button
        run_btn = QPushButton("Run Pipeline")
        run_btn.clicked.connect(self.run_pipeline)
        layout.addWidget(run_btn)
        
        return widget

    def _create_right_panel(self) -> QWidget:
        """Create right panel with enhanced visualization."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.visualization_widget = EnhancedVisualizationWidget(registry=self.plugin_registry)
        layout.addWidget(self.visualization_widget)
        
        # Export buttons at bottom
        button_layout = QHBoxLayout()
        export_data_btn = QPushButton("Export Results")
        export_data_btn.setToolTip("Export fitting parameters, average curve, and average indentation to CSV files")
        export_data_btn.clicked.connect(self.export_data)
        export_plot_btn = QPushButton("Export Plot")
        export_plot_btn.clicked.connect(self.export_plot)
        
        button_layout.addWidget(export_data_btn)
        button_layout.addWidget(export_plot_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget

    def _setup_status_bar(self) -> None:
        """Setup status bar at bottom of window."""
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("Ready")

    def show_experiment_info(self) -> None:
        """Show loaded experiment, cantilever, and tip details."""
        if self.current_dataset is None or len(self.current_dataset) == 0:
            QMessageBox.information(self, "Experiment Info", "No experiment loaded.")
            return

        curve = self.current_curve or self.current_dataset[0]
        tip = curve.tip_geometry

        lines = [
            f"Dataset: {self.current_dataset.name}",
            f"Number of curves: {len(self.current_dataset)}",
            "",
            "Current Curve",
            f"- Index: {curve.index}",
            f"- Spring constant (N/m): {curve.spring_constant:g}",
            "",
            "Tip Geometry",
            f"- Type: {tip.geometry_type}",
        ]

        if tip.radius is not None:
            lines.append(f"- Radius (m): {tip.radius:g}")
        if tip.angle is not None:
            lines.append(f"- Angle (deg): {tip.angle:g}")

        QMessageBox.information(self, "Experiment Info", "\n".join(lines))

    def open_curve(self) -> None:
        """Open an AFM experiment file (JSON or HDF5)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open AFM Experiment",
            "",
            "HDF5 Files (*.h5 *.hdf5);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.statusBar().showMessage(f"Loading {Path(file_path).name}...")
                
                # Load using core io module
                data = loaders.load(file_path)
                
                # Create dataset from loaded data
                self.current_dataset = Dataset(name=Path(file_path).stem)
                
                if "curves" in data:
                    for i, curve_dict in enumerate(data.get("curves", [])):
                        # Handle both nested and flat data structures
                        if "data" in curve_dict:
                            Z = np.array(curve_dict["data"].get("Z", []))
                            F = np.array(curve_dict["data"].get("F", []))
                        else:
                            Z = np.array(curve_dict.get("Z", []))
                            F = np.array(curve_dict.get("F", []))
                        
                        k = float(curve_dict.get("spring_constant", 0.032)) if curve_dict.get("spring_constant") is not None else 0.032
                        
                        from softmech.core.data import TipGeometry
                        tip_dict = curve_dict.get("tip", {})
                        # Handle None values for tip geometry
                        radius = tip_dict.get("radius", 1e-6)
                        if radius is not None:
                            try:
                                radius = float(radius)
                            except (ValueError, TypeError):
                                radius = 1e-6
                        else:
                            radius = 1e-6
                        
                        tip_geom = TipGeometry(
                            geometry_type=tip_dict.get("geometry", "sphere"),
                            radius=radius
                        )
                        
                        curve = Curve(Z, F, spring_constant=k, tip_geometry=tip_geom, index=i)
                        
                        # Load outlier flag (backwards compatible)
                        curve.is_outlier = curve_dict.get("is_outlier", False)

                        # Load persisted fitted force-model parameters if available.
                        if "force_model_params" in curve_dict:
                            curve.set_force_model_params(curve_dict.get("force_model_params"))

                        # Load contact point if available.
                        cp = curve_dict.get("contact_point")
                        if isinstance(cp, (list, tuple)) and len(cp) == 2:
                            try:
                                curve.set_contact_point(float(cp[0]), float(cp[1]))
                            except Exception:
                                pass
                        
                        self.current_dataset.append(curve)
                        
                        if i == 0:
                            self.current_curve = curve
                
                self.statusBar().showMessage(f"Loaded {Path(file_path).name} ({len(self.current_dataset)} curves)")
                logger.info(f"Opened {file_path}")

                self._ensure_pipeline()
                self._update_visualization()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load curve: {str(e)}")
                logger.error(f"Error loading curve: {e}")
                self.statusBar().showMessage("Error loading file")

    def save_pipeline(self) -> None:
        """Save current pipeline to .pipe file."""
        if self.pipeline is None:
            QMessageBox.warning(self, "Warning", "No pipeline to save. Create steps first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pipeline",
            "",
            "Pipeline Files (*.pipe)"
        )
        
        if file_path:
            try:
                self.pipeline.save(file_path)
                self.current_pipeline_file = Path(file_path)
                self.statusBar().showMessage(f"Saved pipeline: {Path(file_path).name}")
                logger.info(f"Saved pipeline to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save pipeline: {str(e)}")
                logger.error(f"Error saving pipeline: {e}")

    def load_pipeline(self) -> None:
        """Load pipeline from .pipe file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Pipeline",
            "",
            "Pipeline Files (*.pipe)"
        )
        
        if file_path:
            try:
                self.pipeline = PipelineDescriptor.load(file_path)
                self.current_pipeline_file = Path(file_path)
                if self.pipeline_editor:
                    self.pipeline_editor.set_pipeline(self.pipeline)
                self.statusBar().showMessage(f"Loaded pipeline: {Path(file_path).name}")
                logger.info(f"Loaded pipeline from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load pipeline: {str(e)}")
                logger.error(f"Error loading pipeline: {e}")

    def save_dataset(self) -> None:
        """Save current dataset with outlier flags to file."""
        if self.current_dataset is None or len(self.current_dataset) == 0:
            QMessageBox.warning(self, "Warning", "No dataset to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Dataset",
            "",
            "HDF5 Files (*.h5 *.hdf5);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.statusBar().showMessage(f"Saving dataset to {Path(file_path).name}...")
                loaders.save(file_path, self.current_dataset)
                self.statusBar().showMessage(f"Saved dataset: {Path(file_path).name} ({len(self.current_dataset)} curves)")
                logger.info(f"Saved dataset to {file_path}")
                
                # Show confirmation with outlier count
                outlier_count = sum(1 for curve in self.current_dataset if curve.is_outlier)
                msg = f"Dataset saved successfully.\n\n"
                msg += f"Total curves: {len(self.current_dataset)}\n"
                msg += f"Outliers: {outlier_count}\n"
                msg += f"Normal curves: {len(self.current_dataset) - outlier_count}"
                QMessageBox.information(self, "Dataset Saved", msg)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save dataset: {str(e)}")
                logger.error(f"Error saving dataset: {e}")

    def export_data(self) -> None:
        """Export analysis results: fitting parameters, average curves, and average indentation."""
        if self.current_dataset is None or len(self.current_dataset) == 0:
            QMessageBox.warning(self, "Warning", "No dataset loaded.")
            return
        
        # Get base file path (without extension)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Results",
            "",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        # Remove .csv extension if present to use as base name
        base_path = Path(file_path)
        if base_path.suffix.lower() == '.csv':
            base_path = base_path.with_suffix('')
        
        try:
            # Filter out outliers
            valid_curves = [c for c in self.current_dataset if not c.is_outlier]
            
            if len(valid_curves) == 0:
                QMessageBox.warning(self, "Warning", "No valid curves (all marked as outliers).")
                return
            
            self.statusBar().showMessage(f"Exporting analysis results ({len(valid_curves)} curves)...")
            
            # 1. Export fitting parameters
            self._export_fitting_parameters(valid_curves, f"{base_path}_data.csv")
            
            # 2. Export average force-displacement curve
            self._export_average_curve(valid_curves, f"{base_path}_curve.csv")
            
            # 3. Export average indentation curve
            self._export_average_indentation(valid_curves, f"{base_path}_indentation.csv")
            
            msg = f"Exported analysis results:\n"
            msg += f"  • {base_path.name}_data.csv (fitting parameters)\n"
            msg += f"  • {base_path.name}_curve.csv (average curve ± std)\n"
            msg += f"  • {base_path.name}_indentation.csv (average indentation ± std)\n"
            msg += f"\nCurves included: {len(valid_curves)} (outliers excluded)"
            
            self.statusBar().showMessage(f"Exported: {base_path.name}_*.csv")
            QMessageBox.information(self, "Export Complete", msg)
            logger.info(f"Exported analysis results to {base_path}_*.csv")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
            logger.error(f"Error exporting data: {e}")

    def _export_fitting_parameters(self, curves, filename: str) -> None:
        """Export fitting parameters from all curves."""
        import csv
        
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            
            # Collect all parameters
            param_data = []
            header = ["curve_index"]
            
            for curve in curves:
                row = [curve.index]
                
                # Force model parameters
                force_params = curve.get_force_model_params()
                if force_params is not None:
                    if len(param_data) == 0:  # First curve with params - set headers
                        if hasattr(force_params, '__dict__'):
                            for key in force_params.__dict__.keys():
                                header.append(f"force_{key}")
                        elif isinstance(force_params, dict):
                            for key in force_params.keys():
                                header.append(f"force_{key}")
                    
                    # Add values
                    if hasattr(force_params, '__dict__'):
                        for val in force_params.__dict__.values():
                            row.append(val)
                    elif isinstance(force_params, dict):
                        for val in force_params.values():
                            row.append(val)
                
                # Elastic model parameters
                elastic_params = curve.get_elastic_model_params()
                if elastic_params is not None:
                    if len(param_data) == 0:  # First curve - add to headers
                        if hasattr(elastic_params, '__dict__'):
                            for key in elastic_params.__dict__.keys():
                                header.append(f"elastic_{key}")
                        elif isinstance(elastic_params, dict):
                            for key in elastic_params.keys():
                                header.append(f"elastic_{key}")
                    
                    # Add values
                    if hasattr(elastic_params, '__dict__'):
                        for val in elastic_params.__dict__.values():
                            row.append(val)
                    elif isinstance(elastic_params, dict):
                        for val in elastic_params.values():
                            row.append(val)
                
                param_data.append(row)
            
            # Write header and data
            if len(param_data) > 0:
                writer.writerow(header)
                writer.writerows(param_data)
            else:
                # No fitting parameters found
                writer.writerow(["curve_index", "note"])
                writer.writerow(["-", "No fitting parameters found"])

    def _export_average_curve(self, curves, filename: str) -> None:
        """Export average force-displacement curve with std deviation."""
        import csv
        
        # Collect all curves (align to CP if available)
        Z_all, F_all = [], []
        
        for curve in curves:
            Z, F = curve.get_current_data()
            cp = curve.get_contact_point()
            
            # Align to contact point if available
            if cp is not None:
                z_cp, f_cp = cp
                Z = Z - z_cp
                F = F - f_cp
            
            Z_all.append(Z)
            F_all.append(F)
        
        if len(Z_all) == 0:
            return
        
        # Find common range
        Z_min = max(z.min() for z in Z_all)
        Z_max = min(z.max() for z in Z_all)
        
        if Z_max <= Z_min:
            # No overlap - just save individual curves
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Z(m)", "F(N)", "note"])
                writer.writerow(["-", "-", "No overlap between curves"])
            return
        
        # Interpolate to common grid
        Z_common = np.linspace(Z_min, Z_max, 500)
        F_interp = np.array([np.interp(Z_common, Z, F) for Z, F in zip(Z_all, F_all)])
        
        F_avg = np.mean(F_interp, axis=0)
        F_std = np.std(F_interp, axis=0)
        
        # Write CSV
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Z(m)", "F_avg(N)", "F_std(N)"])
            for i in range(len(Z_common)):
                writer.writerow([Z_common[i], F_avg[i], F_std[i]])

    def _export_average_indentation(self, curves, filename: str) -> None:
        """Export average indentation curve with std deviation."""
        import csv
        
        # Collect all indentation curves
        indent_all, force_all = [], []
        
        for curve in curves:
            indent, force = curve.get_indentation_data()
            if indent is not None and force is not None:
                indent_all.append(indent)
                force_all.append(force)
        
        if len(indent_all) == 0:
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["indentation(m)", "F(N)", "note"])
                writer.writerow(["-", "-", "No indentation data available"])
            return
        
        # Find common range
        indent_min = max(i.min() for i in indent_all)
        indent_max = min(i.max() for i in indent_all)
        
        if indent_max <= indent_min:
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["indentation(m)", "F(N)", "note"])
                writer.writerow(["-", "-", "No overlap between curves"])
            return
        
        # Interpolate to common grid
        indent_common = np.linspace(indent_min, indent_max, 500)
        force_interp = np.array([np.interp(indent_common, indent, force) 
                                 for indent, force in zip(indent_all, force_all)])
        
        force_avg = np.mean(force_interp, axis=0)
        force_std = np.std(force_interp, axis=0)
        
        # Write CSV
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["indentation(m)", "F_avg(N)", "F_std(N)"])
            for i in range(len(indent_common)):
                writer.writerow([indent_common[i], force_avg[i], force_std[i]])

    def export_plot(self) -> None:
        """Export current visualization as PNG."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            "PNG Files (*.png)"
        )
        
        if file_path:
            if self.visualization_widget and self.visualization_widget.export_current_plot(file_path):
                self.statusBar().showMessage(f"Plot exported: {Path(file_path).name}")
                logger.info(f"Plot exported to {file_path}")
            else:
                QMessageBox.warning(self, "Warning", "No plot available to export.")

    def _ensure_pipeline(self) -> None:
        if self.pipeline is None:
            self.pipeline = self._create_default_pipeline()
        if self.pipeline_editor:
            self.pipeline_editor.set_pipeline(self.pipeline)

    def _reset_pipeline_defaults(self) -> None:
        self.pipeline = self._create_default_pipeline()
        if self.pipeline_editor:
            self.pipeline_editor.set_pipeline(self.pipeline)
        self.statusBar().showMessage("Reset pipeline to defaults")

    def _create_default_pipeline(self) -> PipelineDescriptor:
        metadata = PipelineMetadata(
            name="Default Pipeline",
            description="Default pipeline with none placeholders",
        )

        preprocessing = PipelineStage(name="preprocessing", description="Filtering and contact point")
        preprocessing.add_step(self._make_step("filter", "none"))
        preprocessing.add_step(self._make_step("contact_point", "none"))
        
        analysis = PipelineStage(name="analysis", description="Model fitting")
        analysis.add_step(self._make_step("force_model", "none"))
        # Note: Indentation is auto-calculated after CP detection

        return PipelineDescriptor(metadata=metadata, stages=[preprocessing, analysis])

    def _make_step(self, step_type: str, plugin_id: str) -> PipelineStep:
        plugin_info = self.plugin_registry.get_info(plugin_id)
        return PipelineStep(
            type=step_type,
            plugin_id=plugin_id,
            plugin_version=plugin_info.get("version", "1.0.0"),
            parameters={},
        )

    def _update_visualization(self) -> None:
        if self.visualization_widget:
            self.visualization_widget.set_dataset(self.current_dataset)

    def _on_pipeline_changed(self, pipeline: PipelineDescriptor) -> None:
        """Handle pipeline changes from flowchart editor."""
        self.pipeline = pipeline
        self.statusBar().showMessage("Pipeline modified - Click 'Run Pipeline' to apply changes")
        
        # Auto-run if real-time update is enabled
        if hasattr(self, 'realtime_cb') and self.realtime_cb.isChecked():
            if self.current_dataset is not None and len(self.current_dataset) > 0:
                self.run_pipeline()

    def run_pipeline(self) -> None:
        if self.current_dataset is None or len(self.current_dataset) == 0:
            QMessageBox.warning(self, "Warning", "No dataset loaded.")
            return

        self._ensure_pipeline()
        
        # Change cursor to hourglass to indicate processing
        app = QApplication.instance()
        if app:
            app.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        # Block pipeline_changed signals during execution to prevent UI flashing
        if self.pipeline_editor:
            self.pipeline_editor.blockSignals(True)

        # Preserve fitted parameters for outliers so they remain visible in
        # fitted-parameter scatter plots when force_model is skipped for outliers.
        preserved_outlier_params = {}
        for i, curve in enumerate(self.current_dataset):
            if curve.is_outlier:
                preserved_outlier_params[i] = curve.get_force_model_params()

        for curve in self.current_dataset:
            curve.reset_to_raw()

        progress = QProgressDialog("Running pipeline...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)

        def on_progress(message: str, value: float) -> None:
            progress.setLabelText(message)
            progress.setValue(int(value * 100))
            QCoreApplication.processEvents()
            if progress.wasCanceled():
                raise RuntimeError("Pipeline canceled by user")

        try:
            executor = PipelineExecutor(self.plugin_registry)
            executor.execute(self.pipeline, self.current_dataset, on_progress)

            # Restore outlier fitted parameters that may have been loaded/saved
            # previously, since outliers are intentionally skipped in force_model.
            for i, params in preserved_outlier_params.items():
                if i < len(self.current_dataset) and params is not None:
                    self.current_dataset[i].set_force_model_params(params)

            progress.close()
            
            # Verify data integrity after execution
            valid_curves = 0
            for curve in self.current_dataset:
                Z, F = curve.get_current_data()
                if len(Z) > 0 and len(F) > 0:
                    valid_curves += 1
            
            logger.info(f"Pipeline completed: {valid_curves}/{len(self.current_dataset)} curves have data")
            
            self._update_visualization()
            self.statusBar().showMessage(f"Pipeline completed - {valid_curves}/{len(self.current_dataset)} curves processed")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Pipeline failed: {str(e)}")
            logger.error(f"Pipeline execution error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Restore normal cursor
            app = QApplication.instance()
            if app:
                app.restoreOverrideCursor()
            # Re-enable signals after execution
            if self.pipeline_editor:
                self.pipeline_editor.blockSignals(False)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SoftMech Designer",
            "SoftMech Designer v0.1.0\n\n"
            "Interactive AFM Analysis Pipeline Builder\n\n"
            "Build, test, and save analysis pipelines for "
            "atomic force microscopy nanoindentation data."
        )


def main():
    """Run the Designer application."""
    from PySide6.QtWidgets import QApplication
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s - %(levelname)s - %(message)s"
    )
    
    app = QApplication(sys.argv)
    window = DesignerMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
