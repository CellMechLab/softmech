"""Enhanced visualization widget supporting multi-curve display and data browsers."""

from typing import Optional, List
import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QSlider, QLabel, 
    QSpinBox, QComboBox, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from softmech.core.data import Curve, Dataset

logger = logging.getLogger(__name__)


class MultiCurveViewer(QWidget):
    """View all curves with average and individual curve selection."""

    curve_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)

        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Select curve:"))

        self.curve_slider = QSlider(Qt.Orientation.Horizontal)
        self.curve_slider.setMinimum(0)
        self.curve_slider.sliderMoved.connect(self._on_slider_moved)
        controls.addWidget(self.curve_slider)

        self.curve_spin = QSpinBox()
        self.curve_spin.valueChanged.connect(self._on_spin_changed)
        controls.addWidget(self.curve_spin)

        self.show_average_cb = QComboBox()
        self.show_average_cb.addItems(["Show All", "Show Average Only", "Show Selected Only"])
        self.show_average_cb.currentIndexChanged.connect(self._refresh_plot)
        controls.addWidget(self.show_average_cb)

        self.align_cp_cb = QCheckBox("Align to CP")
        self.align_cp_cb.setToolTip("Shift all curves to align at contact point")
        self.align_cp_cb.stateChanged.connect(self._refresh_plot)
        controls.addWidget(self.align_cp_cb)

        layout.addLayout(controls)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.showGrid(True, True, 0.3)
        self.plot.addLegend(offset=(10, 10))
        self.plot.setLabel("bottom", "Displacement", units="um")
        self.plot.setLabel("left", "Force", units="nN")
        self.plot.setTitle("Force vs Displacement")
        layout.addWidget(self.plot)

        self._dataset: Optional[Dataset] = None
        self._current_index: int = 0

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        self._dataset = dataset
        if dataset:
            self.curve_slider.setMaximum(len(dataset) - 1)
            self.curve_spin.setMaximum(len(dataset) - 1)
            self._current_index = 0
            self.curve_slider.setValue(0)
        self._refresh_plot()

    def _on_slider_moved(self, value: int) -> None:
        self.curve_spin.blockSignals(True)
        self.curve_spin.setValue(value)
        self.curve_spin.blockSignals(False)
        self._current_index = value
        self.curve_selected.emit(value)
        self._refresh_plot()

    def _on_spin_changed(self, value: int) -> None:
        self.curve_slider.blockSignals(True)
        self.curve_slider.setValue(value)
        self.curve_slider.blockSignals(False)
        self._current_index = value
        self.curve_selected.emit(value)
        self._refresh_plot()

    def _refresh_plot(self) -> None:
        self.plot.clear()
        self.plot.addLegend(offset=(10, 10))

        if not self._dataset or len(self._dataset) == 0:
            return

        view_mode = self.show_average_cb.currentText()

        # Show all individual curves (if applicable)
        if view_mode == "Show All":
            self._plot_all_curves()

        # Show average (if applicable)
        if view_mode in ("Show All", "Show Average Only"):
            self._plot_average()

        # Show selected curve (if applicable)
        if view_mode == "Show Selected Only":
            self._plot_selected_curve()
        elif view_mode == "Show All":
            # Highlight selected curve in "Show All" mode
            self._plot_selected_curve_highlighted()

    def _plot_all_curves(self) -> None:
        """Plot all individual curves with transparency."""
        if not self._dataset:
            return

        align_cp = self.align_cp_cb.isChecked()

        for i, curve in enumerate(self._dataset):
            Z, F = curve.get_current_data()
            
            # Apply CP alignment if requested
            if align_cp:
                cp = curve.get_contact_point()
                if cp:
                    z_cp, f_cp = cp
                    Z = Z - z_cp
                    F = F - f_cp

            # Plot with transparency (light gray)
            self.plot.plot(
                Z * 1e6,
                F * 1e9,
                pen=pg.mkPen((150, 150, 150, 100), width=1),
                name=None if i > 0 else "Individual curves"
            )

    def _plot_average(self) -> None:
        """Plot average curve (only in non-aligned mode)."""
        if not self._dataset:
            return

        # Skip average in CP-aligned mode (doesn't make sense)
        if self.align_cp_cb.isChecked():
            return

        Z_all = []
        F_all = []

        for curve in self._dataset:
            Z, F = curve.get_current_data()
            Z_all.append(Z)
            F_all.append(F)

        if not Z_all:
            return

        # Find common Z range
        Z_min = max(z.min() for z in Z_all)
        Z_max = min(z.max() for z in Z_all)

        # Interpolate all curves to common Z
        Z_common = np.linspace(Z_min, Z_max, 500)
        F_interp = []

        for Z, F in zip(Z_all, F_all):
            F_interp.append(np.interp(Z_common, Z, F))

        F_avg = np.mean(F_interp, axis=0)

        self.plot.plot(
            Z_common * 1e6,
            F_avg * 1e9,
            pen=pg.mkPen((0, 0, 0), width=3),
            name="Average",
        )

    def _plot_selected_curve(self) -> None:
        """Plot only the selected curve (for Show Selected Only mode)."""
        if not self._dataset or self._current_index >= len(self._dataset):
            return

        curve = self._dataset[self._current_index]
        Z_raw = curve.raw_data.Z
        F_raw = curve.raw_data.F
        Z_cur, F_cur = curve.get_current_data()

        # Convert to display units
        Z_raw_um = Z_raw * 1e6
        F_raw_nN = F_raw * 1e9
        Z_cur_um = Z_cur * 1e6
        F_cur_nN = F_cur * 1e9

        # Plot raw data as dots
        self.plot.plot(
            Z_raw_um,
            F_raw_nN,
            pen=None,
            symbol='o',
            symbolSize=3,
            symbolBrush=(180, 180, 180, 150),
            symbolPen=None,
            name="Raw data",
        )

        # Plot filtered/processed data as line (if different from raw)
        if not np.array_equal(Z_raw, Z_cur) or not np.array_equal(F_raw, F_cur):
            self.plot.plot(
                Z_cur_um,
                F_cur_nN,
                pen=pg.mkPen((0, 92, 185), width=2),
                name="Filtered",
            )

        # Show contact point if available
        cp = curve.get_contact_point()
        if cp:
            z_cp, f_cp = cp
            self.plot.plot(
                [z_cp * 1e6],
                [f_cp * 1e9],
                pen=None,
                symbol="o",
                symbolSize=12,
                symbolBrush=(200, 60, 60),
                symbolPen=pg.mkPen((100, 30, 30), width=2),
                name="Contact Point",
            )

    def _plot_selected_curve_highlighted(self) -> None:
        """Plot selected curve with strong highlight (for Show All mode)."""
        if not self._dataset or self._current_index >= len(self._dataset):
            return

        curve = self._dataset[self._current_index]
        Z, F = curve.get_current_data()

        align_cp = self.align_cp_cb.isChecked()
        if align_cp:
            cp = curve.get_contact_point()
            if cp:
                z_cp, f_cp = cp
                Z = Z - z_cp
                F = F - f_cp

        self.plot.plot(
            Z * 1e6,
            F * 1e9,
            pen=pg.mkPen((0, 92, 185), width=3),
            name=f"Selected (Curve {self._current_index})",
        )

        # Show CP marker if not aligned
        if not align_cp:
            cp = curve.get_contact_point()
            if cp:
                z_cp, f_cp = cp
                self.plot.plot(
                    [z_cp * 1e6],
                    [f_cp * 1e9],
                    pen=None,
                    symbol="o",
                    symbolSize=10,
                    symbolBrush=(200, 60, 60),
                    name="Contact Point",
                )


class AverageCurveViewer(QWidget):
    """View average curve with standard deviation bands (requires CP calculation)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)

        # Info label
        self.info_label = QLabel("Average curve requires contact point calculation")
        self.info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.info_label)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.showGrid(True, True, 0.3)
        self.plot.addLegend(offset=(10, 10))
        self.plot.setLabel("bottom", "Indentation", units="um")
        self.plot.setLabel("left", "Force", units="nN")
        self.plot.setTitle("Average Curve with Standard Deviation")
        layout.addWidget(self.plot)

        self._dataset: Optional[Dataset] = None

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        self._dataset = dataset
        self._refresh_plot()

    def _refresh_plot(self) -> None:
        self.plot.clear()
        self.plot.addLegend(offset=(10, 10))

        if not self._dataset or len(self._dataset) == 0:
            self.info_label.setText("No dataset loaded")
            return

        # Check if contact points are calculated
        curves_with_cp = [c for c in self._dataset if c.get_contact_point() is not None]
        
        if len(curves_with_cp) == 0:
            self.info_label.setText("Contact point not calculated for any curves. Run pipeline first.")
            return

        self.info_label.setText(f"Showing average of {len(curves_with_cp)} curves with contact point")

        # Collect all curves shifted to CP
        Z_all = []
        F_all = []

        for curve in curves_with_cp:
            Z, F = curve.get_current_data()
            cp = curve.get_contact_point()
            if cp:
                z_cp, f_cp = cp
                # Shift to CP origin
                Z_shifted = Z - z_cp
                F_shifted = F - f_cp
                
                # Only keep indentation region (Z >= 0 after shift)
                mask = Z_shifted >= 0
                if np.any(mask):
                    Z_all.append(Z_shifted[mask])
                    F_all.append(F_shifted[mask])

        if not Z_all:
            self.info_label.setText("No valid indentation data after CP alignment")
            return

        # Find common indentation range (must be covered by all curves)
        Z_min = max(z.min() for z in Z_all)
        Z_max = min(z.max() for z in Z_all)

        if Z_max <= Z_min:
            self.info_label.setText("Insufficient overlap in indentation range")
            return

        # Interpolate all curves to common grid
        Z_common = np.linspace(Z_min, Z_max, 500)
        F_interp = []

        for Z, F in zip(Z_all, F_all):
            F_interp.append(np.interp(Z_common, Z, F))

        F_interp = np.array(F_interp)
        F_avg = np.mean(F_interp, axis=0)
        F_std = np.std(F_interp, axis=0)

        # Convert to display units
        Z_um = Z_common * 1e6
        F_avg_nN = F_avg * 1e9
        F_std_nN = F_std * 1e9

        # Plot std bands (lighter fill)
        upper = F_avg_nN + F_std_nN
        lower = F_avg_nN - F_std_nN
        
        # Create fill between curves using FillBetweenItem
        from pyqtgraph import FillBetweenItem
        curve_upper = pg.PlotCurveItem(Z_um, upper, pen=None)
        curve_lower = pg.PlotCurveItem(Z_um, lower, pen=None)
        fill = FillBetweenItem(curve_upper, curve_lower, brush=(0, 92, 185, 50))
        self.plot.addItem(fill)
        
        # Plot std boundary lines (dashed)
        self.plot.plot(
            Z_um,
            upper,
            pen=pg.mkPen((0, 92, 185, 100), width=1, style=Qt.PenStyle.DashLine),
            name="± 1 Std Dev"
        )
        self.plot.plot(
            Z_um,
            lower,
            pen=pg.mkPen((0, 92, 185, 100), width=1, style=Qt.PenStyle.DashLine),
        )

        # Plot average curve (solid line)
        self.plot.plot(
            Z_um,
            F_avg_nN,
            pen=pg.mkPen((0, 92, 185), width=3),
            name="Average",
        )


class EnhancedVisualizationWidget(QWidget):
    """Multi-tab visualization with dataset browser, curves, indentation, elasticity, and results."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Multi-curve viewer
        self.multi_curve_viewer = MultiCurveViewer()
        self.tabs.addTab(self.multi_curve_viewer, "All Curves")

        # Tab 2: Average curve with std bands
        self.average_curve_viewer = AverageCurveViewer()
        self.tabs.addTab(self.average_curve_viewer, "Average Curve")

        # Tab 3: Indentation (individual)
        self.indent_plot = pg.PlotWidget()
        self.indent_plot.showGrid(True, True, 0.3)
        self.indent_plot.setLabel("bottom", "Indentation", units="um")
        self.indent_plot.setLabel("left", "Force", units="nN")
        self.indent_plot.setTitle("Indentation Curve")
        self.tabs.addTab(self.indent_plot, "Indentation")

        # Tab 4: Elasticity spectra (individual)
        self.elastic_plot = pg.PlotWidget()
        self.elastic_plot.showGrid(True, True, 0.3)
        self.elastic_plot.setLabel("bottom", "Indentation", units="um")
        self.elastic_plot.setLabel("left", "Modulus", units="Pa")
        self.elastic_plot.setTitle("Elasticity Spectra")
        self.elastic_plot.setLogMode(y=True)
        self.tabs.addTab(self.elastic_plot, "Elasticity")

        # Tab 5: Results histogram/grid
        self.results_widget = self._create_results_widget()
        self.tabs.addTab(self.results_widget, "Results")

        self._dataset: Optional[Dataset] = None
        self._current_curve: Optional[Curve] = None

        # Connect curve selection from multi-curve viewer
        self.multi_curve_viewer.curve_selected.connect(self._on_curve_selected)

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        self._dataset = dataset
        self.multi_curve_viewer.set_dataset(dataset)
        self.average_curve_viewer.set_dataset(dataset)
        if dataset and len(dataset) > 0:
            self._current_curve = dataset[0]
            self._refresh_single_curve_plots()

    def _on_curve_selected(self, index: int) -> None:
        if self._dataset and index < len(self._dataset):
            self._current_curve = self._dataset[index]
            self._refresh_single_curve_plots()

    def _refresh_single_curve_plots(self) -> None:
        if not self._current_curve:
            self._clear_plots()
            return

        self._plot_indentation()
        self._plot_elasticity()

    def _plot_indentation(self) -> None:
        self.indent_plot.clear()

        if not self._current_curve:
            return

        indentation, force = self._current_curve.get_indentation_data()
        if indentation is None or force is None:
            text = pg.TextItem("No indentation data", color=(150, 150, 150))
            self.indent_plot.addItem(text)
            return

        self.indent_plot.plot(
            indentation * 1e6,
            force * 1e9,
            pen=pg.mkPen((20, 130, 90), width=2),
        )

    def _plot_elasticity(self) -> None:
        self.elastic_plot.clear()

        if not self._current_curve:
            return

        depth, modulus = self._current_curve.get_elasticity_spectra()
        if depth is None or modulus is None:
            text = pg.TextItem("No elasticity spectra", color=(150, 150, 150))
            self.elastic_plot.addItem(text)
            return

        self.elastic_plot.plot(
            depth * 1e6,
            modulus,
            pen=pg.mkPen((160, 90, 200), width=2),
        )

    def _clear_plots(self) -> None:
        self.indent_plot.clear()
        self.elastic_plot.clear()

    def _create_results_widget(self) -> QWidget:
        """Create results visualization area (histogram/image/table)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Parameter:"))

        self.param_combo = QComboBox()
        self.param_combo.addItems([
            "Young's Modulus (E)",
            "Contact Point (Z_cp)",
            "Force at Contact (F_cp)",
            "Fit Residuals (R²)",
        ])
        self.param_combo.currentIndexChanged.connect(self._refresh_results)
        controls.addWidget(self.param_combo)

        controls.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Histogram", "Table", "Image Map"])
        self.view_combo.currentIndexChanged.connect(self._refresh_results)
        controls.addWidget(self.view_combo)

        controls.addStretch()
        layout.addLayout(controls)

        # Results plot area
        self.results_plot = pg.PlotWidget()
        self.results_plot.setLabel("bottom", "Value")
        self.results_plot.setLabel("left", "Count")
        self.results_plot.setTitle("Results Distribution")
        layout.addWidget(self.results_plot)

        return widget

    def _refresh_results(self) -> None:
        """Update results visualization based on selected parameter and view."""
        self.results_plot.clear()

        if not self._dataset or len(self._dataset) == 0:
            return

        param_name = self.param_combo.currentText()
        view_type = self.view_combo.currentText()

        # Extract values based on parameter
        values = self._extract_parameter_values(param_name)

        if values is None:
            text = pg.TextItem("No data available", color=(150, 150, 150))
            self.results_plot.addItem(text)
            return

        if view_type == "Histogram":
            self._plot_histogram(values, param_name)
        elif view_type == "Table":
            self._plot_table(values, param_name)
        elif view_type == "Image Map":
            self._plot_image_map(values, param_name)

    def _extract_parameter_values(self, param_name: str) -> Optional[np.ndarray]:
        """Extract parameter values from all curves."""
        values = []

        for curve in self._dataset:
            if param_name == "Young's Modulus (E)":
                depth, modulus = curve.get_elasticity_spectra()
                if modulus is not None and len(modulus) > 0:
                    values.append(np.nanmean(modulus))
            elif param_name == "Contact Point (Z_cp)":
                cp = curve.get_contact_point()
                if cp:
                    values.append(cp[0])
            elif param_name == "Force at Contact (F_cp)":
                cp = curve.get_contact_point()
                if cp:
                    values.append(cp[1])

        return np.array(values) if values else None

    def _plot_histogram(self, values: np.ndarray, param_name: str) -> None:
        """Plot histogram of values."""
        if len(values) == 0:
            return

        hist, bin_edges = np.histogram(values, bins=10)
        self.results_plot.plot(
            bin_edges,
            hist,
            stepMode=True,
            fillLevel=0,
            pen=pg.mkPen((0, 92, 185), width=2),
            brush=(0, 92, 185, 100),
        )
        self.results_plot.setLabel("bottom", param_name)
        self.results_plot.setLabel("left", "Count")

    def _plot_table(self, values: np.ndarray, param_name: str) -> None:
        """Display values as a table (placeholder)."""
        # For now, just plot as scatter
        self.results_plot.plot(
            range(len(values)),
            values,
            pen=None,
            symbol="o",
            symbolSize=8,
            symbolBrush=(0, 92, 185),
        )
        self.results_plot.setLabel("bottom", "Curve Index")
        self.results_plot.setLabel("left", param_name)

    def _plot_image_map(self, values: np.ndarray, param_name: str) -> None:
        """Display as 2D image map if spatial coordinates available."""
        # Placeholder: reshape as square grid if possible
        n = len(values)
        side = int(np.sqrt(n))

        if side * side != n:
            # Just show scatter if not square
            self.results_plot.plot(
                range(n),
                values,
                pen=None,
                symbol="s",
                symbolSize=6,
                symbolBrush=(160, 90, 200),
            )
            return

        grid = values.reshape((side, side))
        img = pg.ImageItem(grid)
        self.results_plot.addItem(img)
        self.results_plot.setLabel("bottom", "X")
        self.results_plot.setLabel("left", "Y")

    def export_current_plot(self, file_path: str) -> bool:
        """Export active tab as image."""
        current_widget = self.tabs.currentWidget()
        if current_widget is None:
            return False
        pixmap = current_widget.grab()
        return pixmap.save(file_path)
