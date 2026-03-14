"""Enhanced visualization widget with unified curve selector across all tabs."""

from typing import Optional
import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QHBoxLayout, QComboBox
from PySide6.QtCore import Qt
from scipy.stats import gaussian_kde

from softmech.core.data import Curve, Dataset
from softmech.core.plugins.base import ForceModel
from softmech.core.plugins import PluginRegistry
from .curve_selector import CurveSelectorWidget

logger = logging.getLogger(__name__)


class CurveViewerWidget(QWidget):
    """Base viewer with shared curve selector at top."""

    def __init__(self, title: str, x_label: str, y_label: str, x_unit: str, y_unit: str,
                 show_align_cp: bool = False, log_y: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Shared curve selector at top
        self.curve_selector = CurveSelectorWidget(show_align_cp=show_align_cp)
        self.curve_selector.curve_selected.connect(self._on_curve_selected)
        self.curve_selector.view_mode_changed.connect(self._on_view_mode_changed)
        self.curve_selector.outlier_toggled.connect(self._on_outlier_toggle)
        layout.addWidget(self.curve_selector)

        # Plot widget
        self.plot = pg.PlotWidget()
        self.plot.showGrid(True, True, 0.3)
        self.plot.addLegend(offset=(10, 10))
        self.plot.setLabel("bottom", x_label, units=x_unit)
        self.plot.setLabel("left", y_label, units=y_unit)
        self.plot.setTitle(title)
        if log_y:
            self.plot.setLogMode(y=True)
        layout.addWidget(self.plot)

        self.plot.scene().sigMouseClicked.connect(self._on_plot_clicked)

        self._dataset: Optional[Dataset] = None
        self._cp_calculated = False
        self._log_y = log_y
        self._clickable_series: list[tuple[int, np.ndarray, np.ndarray]] = []
        self._autoscale_pending = True

        # Initialize outlier button controls
        self._sync_outlier_controls()

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        """Set the dataset and update controls."""
        self._dataset = dataset
        # Re-arm autoscale only when data is reloaded/recomputed.
        self._autoscale_pending = True
        if dataset and len(dataset) > 0:
            self.curve_selector.set_num_curves(len(dataset))
            # Check if any curve has CP calculated
            self._cp_calculated = any(c.get_contact_point() is not None for c in dataset)
            # Auto-check align CP if CP is calculated
            if self._cp_calculated and self.curve_selector.show_align_cp:
                self.curve_selector.set_align_cp_checked(True)
        else:
            self.curve_selector.set_num_curves(0)
            self._cp_calculated = False
        self._update_outlier_button()
        self._sync_outlier_controls()
        self._refresh_plot()

    def _on_curve_selected(self, index: int) -> None:
        """Handle curve selection change."""
        self._refresh_plot()
        self._update_outlier_button()

    def _on_view_mode_changed(self, mode: str) -> None:
        """Handle view mode change."""
        self._sync_outlier_controls()
        self._update_outlier_button()
        self._refresh_plot()

    def _on_outlier_toggle(self) -> None:
        """Handle outlier toggle button click."""
        if not self._dataset:
            return
        
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            curve.toggle_outlier()
            self._update_outlier_button()
            self._refresh_plot()
            logger.info(f"Curve {idx} outlier status: {curve.is_outlier}")

    def _update_outlier_button(self) -> None:
        """Update outlier button state based on current curve."""
        if not self._dataset:
            self.curve_selector.set_outlier_button_enabled(False)
            self.curve_selector.set_outlier_checked(False)
            self.curve_selector.update_outlier_button_style(False)
            return
        
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            self.curve_selector.set_outlier_checked(curve.is_outlier)
            self.curve_selector.set_outlier_button_enabled(True)
            self.curve_selector.update_outlier_button_style(curve.is_outlier)
        else:
            self.curve_selector.set_outlier_button_enabled(False)
            self.curve_selector.set_outlier_checked(False)
            self.curve_selector.update_outlier_button_style(False)

    def _sync_outlier_controls(self) -> None:
        """Show outlier toggle in all views, but disable in average mode."""
        mode = self.curve_selector.get_view_mode()
        # Button is visible in all modes, but disabled in average mode
        self.curve_selector.outlier_btn.setVisible(True)
        is_average_mode = mode == "average"
        self.curve_selector.outlier_btn.setEnabled(not is_average_mode)

    def _apply_range_from_non_outliers(self, series: list[tuple[np.ndarray, np.ndarray]]) -> None:
        """Autoscale plot based only on non-outlier series to avoid skew."""
        if not self._autoscale_pending:
            return

        if not series:
            return

        x_all = np.concatenate([x for x, _ in series if x is not None and len(x) > 0])
        y_all = np.concatenate([y for _, y in series if y is not None and len(y) > 0])

        if x_all.size == 0 or y_all.size == 0:
            return

        finite_mask = np.isfinite(x_all) & np.isfinite(y_all)
        x_all = x_all[finite_mask]
        y_all = y_all[finite_mask]

        if self._log_y:
            y_all = y_all[y_all > 0]

        if x_all.size == 0 or y_all.size == 0:
            return

        x_min, x_max = float(np.min(x_all)), float(np.max(x_all))
        y_min, y_max = float(np.min(y_all)), float(np.max(y_all))

        if x_max <= x_min or y_max <= y_min:
            return

        x_pad = max((x_max - x_min) * 0.05, 1e-12)
        y_pad = max((y_max - y_min) * 0.05, 1e-12)

        self.plot.setXRange(x_min - x_pad, x_max + x_pad, padding=0)
        self.plot.setYRange(y_min - y_pad, y_max + y_pad, padding=0)
        self.plot.enableAutoRange(x=False, y=False)
        self._autoscale_pending = False

    def _register_clickable_curve(self, curve_idx: int, x: np.ndarray, y: np.ndarray) -> None:
        """Register a plotted curve for click-based selection."""
        if x is None or y is None or len(x) == 0 or len(y) == 0:
            return
        self._clickable_series.append((curve_idx, np.asarray(x), np.asarray(y)))

    def _on_plot_clicked(self, mouse_event) -> None:
        """Select nearest curve when clicking in all-curves mode."""
        if mouse_event.button() != Qt.MouseButton.LeftButton:
            return
        if not self._dataset or self.curve_selector.get_view_mode() != "all":
            return
        if not self._clickable_series:
            return

        view_box = self.plot.getPlotItem().vb
        mouse_point = view_box.mapSceneToView(mouse_event.scenePos())
        x_click = mouse_point.x()
        y_click = mouse_point.y()

        x_range, y_range = self.plot.viewRange()
        x_scale = max(x_range[1] - x_range[0], 1e-12)
        y_scale = max(y_range[1] - y_range[0], 1e-12)

        best_idx = None
        best_dist2 = np.inf

        for curve_idx, x_vals, y_vals in self._clickable_series:
            finite = np.isfinite(x_vals) & np.isfinite(y_vals)
            if not np.any(finite):
                continue
            x_f = x_vals[finite]
            y_f = y_vals[finite]

            dx = (x_f - x_click) / x_scale
            dy = (y_f - y_click) / y_scale
            dist2 = np.min(dx * dx + dy * dy)

            if dist2 < best_dist2:
                best_dist2 = dist2
                best_idx = curve_idx

        if best_idx is not None and best_dist2 <= 0.01:
            self.curve_selector.set_current_index(best_idx)

    def _refresh_plot(self) -> None:
        """Override in subclass to implement specific plotting."""
        pass


class ForceDisplacementViewer(CurveViewerWidget):
    """Force vs Displacement viewer with all/average/selected modes."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Force vs Displacement",
            x_label="Displacement", y_label="Force",
            x_unit="um", y_unit="nN",
            show_align_cp=True,
            parent=parent
        )

    def _refresh_plot(self) -> None:
        self.plot.clear()
        self.plot.addLegend(offset=(10, 10))
        self._clickable_series = []

        if not self._dataset or len(self._dataset) == 0:
            return

        mode = self.curve_selector.get_view_mode()
        align_cp = self.curve_selector.is_align_cp_enabled()

        if mode == "all":
            self._plot_all_curves(align_cp)
        elif mode == "average":
            self._plot_average_with_std(align_cp)
        elif mode == "selected":
            self._plot_selected_curve()

    def _plot_all_curves(self, align_cp: bool) -> None:
        """Plot all curves with transparency (outliers in red)."""
        if not self._dataset:
            return
        
        non_outlier_series = []
            
        for i, curve in enumerate(self._dataset):
            Z, F = curve.get_current_data()
            
            if align_cp:
                cp = curve.get_contact_point()
                if cp:
                    z_cp, f_cp = cp
                    Z = Z - z_cp
                    F = F - f_cp

            # Use red for outliers, gray for normal curves
            color = (200, 60, 60, 100) if curve.is_outlier else (150, 150, 150, 100)
            self.plot.plot(
                Z * 1e6, F * 1e9,
                pen=pg.mkPen(color, width=1),
                name=None if i > 0 else "Individual curves"
            )

            self._register_clickable_curve(i, Z * 1e6, F * 1e9)

            if not curve.is_outlier:
                non_outlier_series.append((Z * 1e6, F * 1e9))

        # Highlight selected curve
        selected_idx = self.curve_selector.get_current_index()
        if selected_idx < len(self._dataset):
            curve = self._dataset[selected_idx]
            Z, F = curve.get_current_data()
            
            if align_cp:
                cp = curve.get_contact_point()
                if cp:
                    z_cp, f_cp = cp
                    Z = Z - z_cp
                    F = F - f_cp

            # Use black thick for non-outlier, red thick for outlier
            line_color = (200, 60, 60) if curve.is_outlier else (0, 0, 0)
            self.plot.plot(
                Z * 1e6, F * 1e9,
                pen=pg.mkPen(line_color, width=3),
                name=f"Selected outlier (Curve {selected_idx})" if curve.is_outlier else f"Selected (Curve {selected_idx})"
            )

            # Show CP if not aligned
            if not align_cp:
                cp = curve.get_contact_point()
                if cp:
                    z_cp, f_cp = cp
                    self.plot.plot(
                        [z_cp * 1e6], [f_cp * 1e9],
                        pen=None, symbol="o", symbolSize=10,
                        symbolBrush=(200, 60, 60),
                        name="Contact Point"
                    )

        self._apply_range_from_non_outliers(non_outlier_series)

    def _plot_average_with_std(self, align_cp: bool) -> None:
        """Plot average curve with std deviation band."""
        if not self._dataset:
            return
            
        Z_all, F_all = [], []

        for curve in self._dataset:
            if curve.is_outlier:
                continue
            Z, F = curve.get_current_data()
            
            if align_cp:
                cp = curve.get_contact_point()
                if cp:
                    z_cp, f_cp = cp
                    # Align to CP but keep full range (including approach region)
                    Z = Z - z_cp
                    F = F - f_cp
            # If not aligning, use original data as-is

            Z_all.append(Z)
            F_all.append(F)

        if not Z_all:
            return

        # Keep context in average mode: render all curves faintly in the background.
        for i, curve in enumerate(self._dataset):
            Z_bg, F_bg = curve.get_current_data()
            if align_cp:
                cp_bg = curve.get_contact_point()
                if cp_bg:
                    z_cp_bg, f_cp_bg = cp_bg
                    Z_bg = Z_bg - z_cp_bg
                    F_bg = F_bg - f_cp_bg

            bg_color = (200, 60, 60, 30) if curve.is_outlier else (120, 120, 120, 30)
            self.plot.plot(
                Z_bg * 1e6, F_bg * 1e9,
                pen=pg.mkPen(bg_color, width=1),
                name=None if i > 0 else "Background curves"
            )

        # Find common range
        Z_min = max(z.min() for z in Z_all)
        Z_max = min(z.max() for z in Z_all)

        if Z_max <= Z_min:
            return

        # Interpolate
        Z_common = np.linspace(Z_min, Z_max, 500)
        F_interp = np.array([np.interp(Z_common, Z, F) for Z, F in zip(Z_all, F_all)])
        
        F_avg = np.mean(F_interp, axis=0)
        F_std = np.std(F_interp, axis=0)

        Z_um = Z_common * 1e6
        F_avg_nN = F_avg * 1e9
        F_std_nN = F_std * 1e9

        # Plot std bands
        upper = F_avg_nN + F_std_nN
        lower = F_avg_nN - F_std_nN
        
        from pyqtgraph import FillBetweenItem, PlotCurveItem
        curve_upper = PlotCurveItem(Z_um, upper, pen=None)
        curve_lower = PlotCurveItem(Z_um, lower, pen=None)
        fill = FillBetweenItem(curve_upper, curve_lower, brush=(0, 92, 185, 50))
        self.plot.addItem(fill)

        # Plot std boundaries
        self.plot.plot(Z_um, upper, pen=pg.mkPen((0, 92, 185, 100), width=1, style=Qt.PenStyle.DashLine), name="± 1 Std Dev")
        self.plot.plot(Z_um, lower, pen=pg.mkPen((0, 92, 185, 100), width=1, style=Qt.PenStyle.DashLine))

        # Plot average
        self.plot.plot(Z_um, F_avg_nN, pen=pg.mkPen((0, 92, 185), width=3), name="Average")
        self._apply_range_from_non_outliers([(Z_um, F_avg_nN), (Z_um, upper), (Z_um, lower)])

    def _plot_selected_curve(self) -> None:
        """Plot single selected curve with raw/filtered."""
        if not self._dataset:
            return
            
        idx = self.curve_selector.get_current_index()
        if idx >= len(self._dataset):
            return

        curve = self._dataset[idx]
        Z_raw = curve.raw_data.Z
        F_raw = curve.raw_data.F
        Z_cur, F_cur = curve.get_current_data()

        # Plot raw as solid gray dots
        self.plot.plot(
            Z_raw * 1e6, F_raw * 1e9,
            pen=None, symbol='o', symbolSize=3,
            symbolBrush=(128, 128, 128), symbolPen=None,
            name="Raw data"
        )

        # Plot filtered as line (or raw if no filtering applied)
        line_color = (200, 60, 60) if curve.is_outlier else (0, 0, 0)
        if not np.array_equal(Z_raw, Z_cur) or not np.array_equal(F_raw, F_cur):
            self.plot.plot(
                Z_cur * 1e6, F_cur * 1e9,
                pen=pg.mkPen(line_color, width=1.5),
                name="Filtered"
            )
        else:
            # If no filter applied, still show line over raw data
            self.plot.plot(
                Z_raw * 1e6, F_raw * 1e9,
                pen=pg.mkPen(line_color, width=1.5),
                name="Data"
            )

        # Show CP
        cp = curve.get_contact_point()
        if cp:
            z_cp, f_cp = cp
            self.plot.plot(
                [z_cp * 1e6], [f_cp * 1e9],
                pen=None, symbol="o", symbolSize=12,
                symbolBrush=(200, 60, 60),
                symbolPen=pg.mkPen((100, 30, 30), width=2),
                name="Contact Point"
            )


class IndentationViewer(CurveViewerWidget):
    """Indentation curve viewer with all/average/selected modes."""

    def __init__(self, registry: Optional[PluginRegistry] = None, parent: Optional[QWidget] = None):
        super().__init__(
            title="Indentation Curve",
            x_label="Indentation", y_label="Force",
            x_unit="um", y_unit="nN",
            show_align_cp=False,  # No CP align for indentation
            parent=parent
        )
        self.registry = registry
        self.fit_params_label = QLabel("Fitted parameters: n/a")
        self.fit_params_label.setStyleSheet("padding: 4px 8px;")
        viewer_layout = self.layout()
        if viewer_layout is not None:
            viewer_layout.addWidget(self.fit_params_label)

    def _refresh_plot(self) -> None:
        self.plot.clear()
        self.plot.addLegend(offset=(10, 10))
        self._clickable_series = []
        self.fit_params_label.setText("Fitted parameters: n/a")

        if not self._dataset or len(self._dataset) == 0:
            return

        mode = self.curve_selector.get_view_mode()

        if mode == "all":
            self._plot_all_curves()
        elif mode == "average":
            self._plot_average_with_std()
        elif mode == "selected":
            self._plot_selected_curve()

    def _plot_all_curves(self) -> None:
        """Plot all indentation curves (outliers in red)."""
        if not self._dataset:
            return
        
        non_outlier_series = []
            
        for i, curve in enumerate(self._dataset):
            indent, force = curve.get_indentation_data()
            if indent is None or force is None:
                continue

            # Use red for outliers, gray for normal curves
            color = (200, 60, 60, 100) if curve.is_outlier else (150, 150, 150, 100)
            self.plot.plot(
                indent * 1e6, force * 1e9,
                pen=pg.mkPen(color, width=1),
                name=None if i > 0 else "Individual curves"
            )

            self._register_clickable_curve(i, indent * 1e6, force * 1e9)

            if not curve.is_outlier:
                non_outlier_series.append((indent * 1e6, force * 1e9))

        # Highlight selected
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            indent, force = curve.get_indentation_data()
            if indent is not None and force is not None:
                # Use black thick for non-outlier, red thick for outlier
                line_color = (200, 60, 60) if curve.is_outlier else (0, 0, 0)
                self.plot.plot(
                    indent * 1e6, force * 1e9,
                    pen=pg.mkPen(line_color, width=3),
                    name=f"Selected outlier (Curve {idx})" if curve.is_outlier else f"Selected (Curve {idx})"
                )

        self._apply_range_from_non_outliers(non_outlier_series)


    def _plot_average_with_std(self) -> None:
        """Plot average indentation with std."""
        if not self._dataset:
            return
            
        indent_all, force_all = [], []

        for curve in self._dataset:
            if curve.is_outlier:
                continue
            indent, force = curve.get_indentation_data()
            if indent is not None and force is not None:
                indent_all.append(indent)
                force_all.append(force)

        if not indent_all:
            return

        # Keep context in average mode: render all curves faintly in the background.
        for i, curve in enumerate(self._dataset):
            indent_bg, force_bg = curve.get_indentation_data()
            if indent_bg is None or force_bg is None:
                continue

            bg_color = (200, 60, 60, 30) if curve.is_outlier else (120, 120, 120, 30)
            self.plot.plot(
                indent_bg * 1e6, force_bg * 1e9,
                pen=pg.mkPen(bg_color, width=1),
                name=None if i > 0 else "Background curves"
            )

        # Common range
        indent_min = max(i.min() for i in indent_all)
        indent_max = min(i.max() for i in indent_all)

        if indent_max <= indent_min:
            return

        indent_common = np.linspace(indent_min, indent_max, 500)
        force_interp = np.array([np.interp(indent_common, i, f) for i, f in zip(indent_all, force_all)])
        
        force_avg = np.mean(force_interp, axis=0)
        force_std = np.std(force_interp, axis=0)

        indent_um = indent_common * 1e6
        force_avg_nN = force_avg * 1e9
        force_std_nN = force_std * 1e9

        # Std bands
        upper = force_avg_nN + force_std_nN
        lower = force_avg_nN - force_std_nN
        
        from pyqtgraph import FillBetweenItem, PlotCurveItem
        curve_upper = PlotCurveItem(indent_um, upper, pen=None)
        curve_lower = PlotCurveItem(indent_um, lower, pen=None)
        fill = FillBetweenItem(curve_upper, curve_lower, brush=(20, 130, 90, 50))
        self.plot.addItem(fill)

        self.plot.plot(indent_um, upper, pen=pg.mkPen((20, 130, 90, 100), width=1, style=Qt.PenStyle.DashLine), name="± 1 Std Dev")
        self.plot.plot(indent_um, lower, pen=pg.mkPen((20, 130, 90, 100), width=1, style=Qt.PenStyle.DashLine))
        self.plot.plot(indent_um, force_avg_nN, pen=pg.mkPen((20, 130, 90), width=3), name="Average")
        self._apply_range_from_non_outliers([(indent_um, force_avg_nN), (indent_um, upper), (indent_um, lower)])

    def _plot_selected_curve(self) -> None:
        """Plot single indentation curve."""
        if not self._dataset:
            return
            
        idx = self.curve_selector.get_current_index()
        if idx >= len(self._dataset):
            return

        curve = self._dataset[idx]
        indent, force = curve.get_indentation_data()
        
        if indent is None or force is None:
            text = pg.TextItem("No indentation data", color=(150, 150, 150))
            self.plot.addItem(text)
            return

        fit_result = self._compute_force_model_fit(curve, indent)
        equation = self._get_model_equation(curve)

        if fit_result is not None:
            fit_x, fit_y = fit_result
            self.fit_params_label.setText(self._format_fitted_parameters(curve))
            marker_color = (200, 60, 60, 150) if curve.is_outlier else (20, 130, 90, 150)
            fit_color = (200, 60, 60) if curve.is_outlier else (40, 40, 40)
            self.plot.plot(
                indent * 1e6, force * 1e9,
                pen=None,
                symbol="o",
                symbolSize=4,
                symbolBrush=marker_color,
                symbolPen=None,
                name=f"Curve {idx} data"
            )
            self.plot.plot(
                fit_x * 1e6, fit_y * 1e9,
                pen=pg.mkPen(fit_color, width=2),
                name=f"Fit ({equation})" if equation else "Fit"
            )
        else:
            self.fit_params_label.setText(self._format_fitted_parameters(curve))
            line_color = (200, 60, 60) if curve.is_outlier else (20, 130, 90)
            self.plot.plot(
                indent * 1e6, force * 1e9,
                pen=pg.mkPen(line_color, width=2),
                name=f"Curve {idx}"
            )

    def _get_model_equation(self, curve: Curve) -> str:
        """Return equation string for selected model, if available."""
        if self.registry is None:
            return ""

        plugin_id = None
        for result in reversed(curve.get_processing_history()):
            if result.step_name == "force_model" and result.plugin_id and result.plugin_id != "none":
                plugin_id = result.plugin_id
                break

        if not plugin_id:
            return ""

        info = self.registry.get_info(plugin_id)
        equation = info.get("equation", "") if isinstance(info, dict) else ""
        return self._format_equation_for_display(equation)

    @staticmethod
    def _format_equation_for_display(equation: str) -> str:
        """Convert common LaTeX-like tokens to readable Unicode for labels/legends."""
        text = (equation or "").strip()
        if not text:
            return ""

        replacements = {
            "\\delta": "δ",
            "\\nu": "ν",
            "\\sqrt": "√",
            "\\frac": "",
            "\\left": "",
            "\\right": "",
            "\\,": " ",
            "^2": "²",
            "^3": "³",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)

        text = text.replace("{", "").replace("}", "")
        text = text.replace("=", " = ")
        return " ".join(text.split())

    def _format_fitted_parameters(self, curve: Curve) -> str:
        """Return a formatted fitted-parameter string for selected curve."""
        fitted_params = curve.get_force_model_params()
        if fitted_params is None:
            return "Fitted parameters: n/a"

        if isinstance(fitted_params, dict):
            items = [f"{key}={value:.4g}" if isinstance(value, (float, int, np.floating, np.integer)) else f"{key}={value}"
                     for key, value in fitted_params.items()]
            return f"Fitted parameters: {', '.join(items)}"

        if isinstance(fitted_params, (list, tuple, np.ndarray)):
            values = []
            for idx, value in enumerate(fitted_params):
                if isinstance(value, (float, int, np.floating, np.integer)):
                    values.append(f"p{idx}={float(value):.4g}")
                else:
                    values.append(f"p{idx}={value}")
            return f"Fitted parameters: {', '.join(values)}"

        if isinstance(fitted_params, (float, int, np.floating, np.integer)):
            return f"Fitted parameters: p0={float(fitted_params):.4g}"

        return f"Fitted parameters: {fitted_params}"

    def _compute_force_model_fit(self, curve: Curve, indent: np.ndarray) -> Optional[tuple[np.ndarray, np.ndarray]]:
        """Compute fitted force curve from stored force-model results within fitting region."""
        if self.registry is None:
            return None

        fitted_params = curve.get_force_model_params()
        if fitted_params is None:
            return None

        last_force_model_step = None
        for result in reversed(curve.get_processing_history()):
            if result.step_name == "force_model" and result.plugin_id and result.plugin_id != "none":
                last_force_model_step = result
                break

        if last_force_model_step is None:
            return None

        try:
            plugin = self.registry.get(last_force_model_step.plugin_id)
            if not isinstance(plugin, ForceModel):
                return None
            if isinstance(last_force_model_step.parameters, dict):
                plugin.set_parameters_dict(last_force_model_step.parameters)

            if isinstance(fitted_params, dict):
                param_values = tuple(fitted_params.values())
            elif isinstance(fitted_params, (list, tuple, np.ndarray)):
                param_values = tuple(fitted_params)
            else:
                param_values = (fitted_params,)

            indent = np.asarray(indent)
            min_nm = float(plugin.get_parameter("min_indentation_depth"))
            max_nm = float(plugin.get_parameter("max_indentation_depth"))

            indent_nm = indent * 1e9
            if min_nm <= 0:
                min_nm = float(np.nanmin(indent_nm)) if np.all(np.isfinite(indent_nm)) else 0.0
            if not np.isfinite(max_nm) or max_nm <= 0:
                max_nm = float(np.nanmax(indent_nm)) if np.all(np.isfinite(indent_nm)) else np.inf

            mask = (indent_nm >= min_nm) & (indent_nm <= max_nm)
            fit_x = indent[mask]
            if fit_x.size == 0:
                return None

            fit_y = plugin.theory(fit_x, *param_values, curve=curve)
            if fit_y is None:
                return None
            fit_y = np.asarray(fit_y)
            if fit_y.shape != fit_x.shape:
                return None
            return fit_x, fit_y
        except Exception as exc:
            logger.debug(f"Could not compute model fit overlay for curve {curve.index}: {exc}")
            return None


class ElasticityViewer(CurveViewerWidget):
    """Elasticity spectra viewer with all/average/selected modes."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Elasticity Spectra",
            x_label="Indentation", y_label="Modulus",
            x_unit="um", y_unit="Pa",
            show_align_cp=False,
            log_y=True,
            parent=parent
        )

    def _refresh_plot(self) -> None:
        self.plot.clear()
        self.plot.addLegend(offset=(10, 10))
        self._clickable_series = []

        if not self._dataset or len(self._dataset) == 0:
            return

        mode = self.curve_selector.get_view_mode()

        if mode == "all":
            self._plot_all_curves()
        elif mode == "average":
            self._plot_average_with_std()
        elif mode == "selected":
            self._plot_selected_curve()

    def _plot_all_curves(self) -> None:
        """Plot all elasticity spectra (outliers in red)."""
        if not self._dataset:
            return
        
        non_outlier_series = []
            
        for i, curve in enumerate(self._dataset):
            depth, modulus = curve.get_elasticity_spectra()
            if depth is None or modulus is None:
                continue

            # Use red for outliers, gray for normal curves
            color = (200, 60, 60, 100) if curve.is_outlier else (150, 150, 150, 100)
            self.plot.plot(
                depth * 1e6, modulus,
                pen=pg.mkPen(color, width=1),
                name=None if i > 0 else "Individual curves"
            )

            self._register_clickable_curve(i, depth * 1e6, modulus)

            if not curve.is_outlier:
                non_outlier_series.append((depth * 1e6, modulus))

        # Highlight selected
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            depth, modulus = curve.get_elasticity_spectra()
            if depth is not None and modulus is not None:
                # Use black thick for non-outlier, red thick for outlier
                line_color = (200, 60, 60) if curve.is_outlier else (0, 0, 0)
                self.plot.plot(
                    depth * 1e6, modulus,
                    pen=pg.mkPen(line_color, width=3),
                    name=f"Selected outlier (Curve {idx})" if curve.is_outlier else f"Selected (Curve {idx})"
                )

        self._apply_range_from_non_outliers(non_outlier_series)

    def _plot_average_with_std(self) -> None:
        """Plot average elasticity with std."""
        if not self._dataset:
            return
            
        depth_all, modulus_all = [], []

        for curve in self._dataset:
            if curve.is_outlier:
                continue
            depth, modulus = curve.get_elasticity_spectra()
            if depth is not None and modulus is not None:
                depth_all.append(depth)
                modulus_all.append(modulus)

        if not depth_all:
            return

        # Common range
        depth_min = max(d.min() for d in depth_all)
        depth_max = min(d.max() for d in depth_all)

        if depth_max <= depth_min:
            return

        depth_common = np.linspace(depth_min, depth_max, 500)
        modulus_interp = np.array([np.interp(depth_common, d, m) for d, m in zip(depth_all, modulus_all)])
        
        modulus_avg = np.mean(modulus_interp, axis=0)
        modulus_std = np.std(modulus_interp, axis=0)

        depth_um = depth_common * 1e6

        # Std bands
        upper = modulus_avg + modulus_std
        lower = modulus_avg - modulus_std
        
        # Plot average first (so it appears on top in legend)
        self.plot.plot(depth_um, modulus_avg, pen=pg.mkPen((160, 90, 200), width=3), name="Average")
        
        # Then plot std bands and fills
        from pyqtgraph import FillBetweenItem, PlotCurveItem
        curve_upper = PlotCurveItem(depth_um, upper, pen=None)
        curve_lower = PlotCurveItem(depth_um, lower, pen=None)
        fill = FillBetweenItem(curve_upper, curve_lower, brush=(160, 90, 200, 50))
        self.plot.addItem(fill)

        self.plot.plot(depth_um, upper, pen=pg.mkPen((160, 90, 200, 100), width=1, style=Qt.PenStyle.DashLine), name="± 1 Std Dev")
        self.plot.plot(depth_um, lower, pen=pg.mkPen((160, 90, 200, 100), width=1, style=Qt.PenStyle.DashLine))
        self._apply_range_from_non_outliers([(depth_um, modulus_avg), (depth_um, upper), (depth_um, lower)])

    def _plot_selected_curve(self) -> None:
        """Plot single elasticity spectrum."""
        if not self._dataset:
            return
            
        idx = self.curve_selector.get_current_index()
        if idx >= len(self._dataset):
            return

        curve = self._dataset[idx]
        depth, modulus = curve.get_elasticity_spectra()
        
        if depth is None or modulus is None:
            text = pg.TextItem("No elasticity data", color=(150, 150, 150))
            self.plot.addItem(text)
            return

        self.plot.plot(
            depth * 1e6, modulus,
            pen=pg.mkPen((200, 60, 60) if curve.is_outlier else (160, 90, 200), width=2),
            name=f"Curve {idx}"
        )


class DataVisualizationViewer(QWidget):
    """Dataset-level force-model fit visualization and summary statistics."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add curve selector at top
        self.curve_selector = CurveSelectorWidget(show_align_cp=False)
        self.curve_selector.curve_selected.connect(self._on_curve_selected)
        self.curve_selector.outlier_toggled.connect(self._on_outlier_toggle)
        # Data visualisation has a fixed view; disable mode switching controls.
        self.curve_selector.view_all_rb.setEnabled(False)
        self.curve_selector.view_average_rb.setEnabled(False)
        self.curve_selector.view_selected_rb.setEnabled(False)
        layout.addWidget(self.curve_selector)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Parameter:"))
        self.parameter_combo = QComboBox()
        self.parameter_combo.currentIndexChanged.connect(self._refresh_plots)
        controls.addWidget(self.parameter_combo)
        controls.addStretch()
        layout.addLayout(controls)

        self.stats_label = QLabel("No fitted parameters available")
        self.stats_label.setStyleSheet("padding: 2px 8px;")
        layout.addWidget(self.stats_label)

        self.scatter_plot = pg.PlotWidget()
        self.scatter_plot.showGrid(True, True, 0.3)
        self.scatter_plot.setLabel("bottom", "Curve Index")
        self.scatter_plot.setLabel("left", "Parameter Value")
        self.scatter_plot.setTitle("Fitted Parameters by Curve")
        self.scatter_plot.scene().sigMouseClicked.connect(self._on_scatter_clicked)
        layout.addWidget(self.scatter_plot)

        self.hist_plot = pg.PlotWidget()
        self.hist_plot.showGrid(True, True, 0.3)
        self.hist_plot.setLabel("bottom", "Parameter Value")
        self.hist_plot.setLabel("left", "Density")
        self.hist_plot.setTitle("Parameter Distribution")
        layout.addWidget(self.hist_plot)

        self._dataset: Optional[Dataset] = None
        self._param_names: list[str] = []
        self._param_matrix: Optional[np.ndarray] = None
        self._curve_indices: Optional[np.ndarray] = None
        self._selected_curve_idx: Optional[int] = None

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        self._dataset = dataset
        if dataset and len(dataset) > 0:
            self.curve_selector.set_num_curves(len(dataset))
        else:
            self.curve_selector.set_num_curves(0)
        self._extract_parameters()
        self._update_outlier_button()
        self._sync_outlier_controls()
        self._refresh_plots()

    def _on_curve_selected(self, index: int) -> None:
        """Handle curve selection from the selector."""
        self._selected_curve_idx = index
        self._update_outlier_button()
        self._refresh_plots()

    def _on_outlier_toggle(self) -> None:
        """Handle outlier toggle button click."""
        if not self._dataset:
            return
        
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            curve.toggle_outlier()
            self._update_outlier_button()
            self._refresh_plots()
            logger.info(f"Curve {idx} outlier status: {curve.is_outlier}")

    def _update_outlier_button(self) -> None:
        """Update outlier button state based on current curve."""
        if not self._dataset:
            self.curve_selector.set_outlier_button_enabled(False)
            self.curve_selector.set_outlier_checked(False)
            self.curve_selector.update_outlier_button_style(False)
            return
        
        idx = self.curve_selector.get_current_index()
        if idx < len(self._dataset):
            curve = self._dataset[idx]
            self.curve_selector.set_outlier_checked(curve.is_outlier)
            self.curve_selector.set_outlier_button_enabled(True)
            self.curve_selector.update_outlier_button_style(curve.is_outlier)
        else:
            self.curve_selector.set_outlier_button_enabled(False)
            self.curve_selector.set_outlier_checked(False)
            self.curve_selector.update_outlier_button_style(False)

    def _sync_outlier_controls(self) -> None:
        """Show outlier toggle in all views, but disable in average mode."""
        mode = self.curve_selector.get_view_mode()
        # Button is visible in all modes, but disabled in average mode
        self.curve_selector.outlier_btn.setVisible(True)
        is_average_mode = mode == "average"
        self.curve_selector.outlier_btn.setEnabled(not is_average_mode)

    def _extract_parameters(self) -> None:
        self._param_names = []
        self._param_matrix = None
        self._curve_indices = None
        self.parameter_combo.blockSignals(True)
        self.parameter_combo.clear()

        if not self._dataset or len(self._dataset) == 0:
            self.parameter_combo.blockSignals(False)
            return

        rows = []
        curve_indices = []
        dict_keys = None
        max_len = 0

        for curve_index, curve in enumerate(self._dataset):
            params = curve.get_force_model_params()
            if params is None:
                continue

            row = None
            if isinstance(params, dict):
                if dict_keys is None:
                    dict_keys = list(params.keys())
                row = [params.get(key, np.nan) for key in dict_keys]
            elif isinstance(params, (list, tuple, np.ndarray)):
                row = list(params)
                max_len = max(max_len, len(row))
            elif isinstance(params, (float, int, np.floating, np.integer)):
                row = [float(params)]
                max_len = max(max_len, 1)

            if row is not None:
                rows.append(row)
                curve_indices.append(curve_index)

        if not rows:
            self.parameter_combo.blockSignals(False)
            return

        if dict_keys is not None:
            self._param_names = dict_keys
            matrix_rows = []
            for row in rows:
                matrix_rows.append([self._safe_float(value) for value in row])
            self._param_matrix = np.asarray(matrix_rows, dtype=float)
        else:
            if max_len == 0:
                max_len = max(len(row) for row in rows)
            self._param_names = [f"p{i}" for i in range(max_len)]
            matrix_rows = []
            for row in rows:
                padded = row + [np.nan] * (max_len - len(row))
                matrix_rows.append([self._safe_float(value) for value in padded])
            self._param_matrix = np.asarray(matrix_rows, dtype=float)

        self._curve_indices = np.asarray(curve_indices, dtype=int)
        self.parameter_combo.addItems(self._param_names)
        self.parameter_combo.blockSignals(False)

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value)
        except Exception:
            return np.nan

    def _refresh_plots(self) -> None:
        self.scatter_plot.clear()
        self.hist_plot.clear()

        if self._param_matrix is None or self._curve_indices is None or self._param_matrix.size == 0:
            self.stats_label.setText("No fitted parameters available")
            return

        param_idx = self.parameter_combo.currentIndex()
        if param_idx < 0 or param_idx >= self._param_matrix.shape[1]:
            self.stats_label.setText("No parameter selected")
            return

        param_name = self._param_names[param_idx]
        values = self._param_matrix[:, param_idx]
        valid_mask = np.isfinite(values)
        values_valid = values[valid_mask]
        curves_valid = self._curve_indices[valid_mask]

        if values_valid.size == 0:
            self.stats_label.setText(f"No valid values for {param_name}")
            return

        # Plot ALL points (including outliers) colored by outlier status
        for i, (curve_idx, value) in enumerate(zip(curves_valid, values_valid)):
            is_outlier = self._dataset[curve_idx].is_outlier if self._dataset else False
            is_selected = curve_idx == self._selected_curve_idx
            
            # Color: red for outliers, blue for normal
            color = (200, 60, 60, 200) if is_outlier else (0, 92, 185, 170)
            size = 10 if is_selected else 7
            pen_color = (0, 0, 0) if is_selected else None
            pen_width = 2 if is_selected else 0
            
            self.scatter_plot.plot(
                [curve_idx],
                [value],
                pen=None,
                symbol="o",
                symbolSize=size,
                symbolBrush=color,
                symbolPen=pg.mkPen(pen_color, width=pen_width) if is_selected else None,
            )

        # For histogram and statistics, exclude outliers
        non_outlier_mask = np.array([not self._dataset[curve_idx].is_outlier 
                                      for curve_idx in curves_valid])
        values_non_outlier = values_valid[non_outlier_mask]

        if values_non_outlier.size == 0:
            self.stats_label.setText(f"{param_name}: No non-outlier data available")
            return

        bins = min(20, max(5, int(np.sqrt(values_non_outlier.size))))
        hist, edges = np.histogram(values_non_outlier, bins=bins, density=True)
        centers = (edges[:-1] + edges[1:]) / 2.0
        widths = np.diff(edges)
        for center, width, height in zip(centers, widths, hist):
            bar = pg.BarGraphItem(x=[center], height=[height], width=width * 0.9, brush=(20, 130, 90, 120), pen=None)
            self.hist_plot.addItem(bar)

        if values_non_outlier.size >= 2 and np.std(values_non_outlier) > 0:
            kde = gaussian_kde(values_non_outlier)
            x_kde = np.linspace(values_non_outlier.min(), values_non_outlier.max(), 300)
            y_kde = kde(x_kde)
            self.hist_plot.plot(x_kde, y_kde, pen=pg.mkPen((40, 40, 40), width=2), name="KDE")

        mean_val = float(np.mean(values_non_outlier))
        std_val = float(np.std(values_non_outlier, ddof=0))
        median_val = float(np.median(values_non_outlier))
        min_val = float(np.min(values_non_outlier))
        max_val = float(np.max(values_non_outlier))
        count = int(values_non_outlier.size)
        outlier_count = int(values_valid.size - values_non_outlier.size)
        
        stats_text = f"{param_name}: n={count}"
        if outlier_count > 0:
            stats_text += f" ({outlier_count} outliers excluded)"
        stats_text += f" | mean={mean_val:.4g} | std={std_val:.4g} | median={median_val:.4g} | min={min_val:.4g} | max={max_val:.4g}"
        self.stats_label.setText(stats_text)

    def _on_scatter_clicked(self, mouse_event) -> None:
        """Handle click on scatter plot to select curve."""
        if mouse_event.button() != Qt.MouseButton.LeftButton:
            return
        if self._param_matrix is None or self._curve_indices is None:
            return

        param_idx = self.parameter_combo.currentIndex()
        if param_idx < 0 or param_idx >= self._param_matrix.shape[1]:
            return

        values = self._param_matrix[:, param_idx]
        valid_mask = np.isfinite(values)
        values_valid = values[valid_mask]
        curves_valid = self._curve_indices[valid_mask]

        if values_valid.size == 0:
            return

        # Get click position in plot coordinates
        view_box = self.scatter_plot.getPlotItem().vb
        mouse_point = view_box.mapSceneToView(mouse_event.scenePos())
        x_click = mouse_point.x()
        y_click = mouse_point.y()

        # Find nearest point
        x_range, y_range = self.scatter_plot.viewRange()
        x_scale = max(x_range[1] - x_range[0], 1)
        y_scale = max(y_range[1] - y_range[0], 1e-12)

        best_idx = None
        best_dist2 = np.inf

        for i, (curve_idx, value) in enumerate(zip(curves_valid, values_valid)):
            dx = (curve_idx - x_click) / x_scale
            dy = (value - y_click) / y_scale
            dist2 = dx * dx + dy * dy

            if dist2 < best_dist2:
                best_dist2 = dist2
                best_idx = int(curve_idx)

        # Select if click is close enough (threshold of 0.02)
        if best_idx is not None and best_dist2 <= 0.02:
            self.curve_selector.set_current_index(best_idx)


class EnhancedVisualizationWidget(QWidget):
    """Multi-tab visualization with unified curve selectors."""

    def __init__(self, registry: Optional[PluginRegistry] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.registry = registry

        # Create viewers
        self.force_viewer = ForceDisplacementViewer()
        self.indent_viewer = IndentationViewer(registry=self.registry)
        self.data_viz_viewer = DataVisualizationViewer()

        self.tabs.addTab(self.force_viewer, "Force vs Displacement")
        self.tabs.addTab(self.indent_viewer, "Indentation")
        self.tabs.addTab(self.data_viz_viewer, "Data Visualisation")

        # Synchronize curve selection across all tabs
        self.force_viewer.curve_selector.curve_selected.connect(self._sync_curve_selection)
        self.indent_viewer.curve_selector.curve_selected.connect(self._sync_curve_selection)
        self.data_viz_viewer.curve_selector.curve_selected.connect(self._sync_curve_selection)

        self._dataset: Optional[Dataset] = None
        self._syncing = False  # Flag to prevent circular updates

    def set_dataset(self, dataset: Optional[Dataset]) -> None:
        """Set dataset for all viewers."""
        self._dataset = dataset
        self.force_viewer.set_dataset(dataset)
        self.indent_viewer.set_dataset(dataset)
        self.data_viz_viewer.set_dataset(dataset)

    def _sync_curve_selection(self, index: int) -> None:
        """Synchronize curve selection across all tabs."""
        if self._syncing:
            return
        
        self._syncing = True
        try:
            # Update all curve selectors to the same index
            if self.force_viewer.curve_selector.get_current_index() != index:
                self.force_viewer.curve_selector.set_current_index(index)
            if self.indent_viewer.curve_selector.get_current_index() != index:
                self.indent_viewer.curve_selector.set_current_index(index)
            if self.data_viz_viewer.curve_selector.get_current_index() != index:
                self.data_viz_viewer.curve_selector.set_current_index(index)
        finally:
            self._syncing = False

    def export_current_plot(self, file_path: str) -> bool:
        """Export current tab's plot."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, CurveViewerWidget):
            pixmap = current_widget.plot.grab()
            return pixmap.save(file_path)
        return False
