"""Visualization widgets for the Designer UI."""

from typing import Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from softmech.core.data import Curve


class VisualizationWidget(QWidget):
    """Tabbed plot area for raw/filtered curves and derived spectra."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.force_plot = pg.PlotWidget()
        self.force_plot.showGrid(True, True, 0.3)
        self.force_plot.addLegend(offset=(10, 10))
        self.force_plot.setLabel("bottom", "Displacement", units="um")
        self.force_plot.setLabel("left", "Force", units="nN")
        self.force_plot.setTitle("Force vs Displacement")

        self.indent_plot = pg.PlotWidget()
        self.indent_plot.showGrid(True, True, 0.3)
        self.indent_plot.setLabel("bottom", "Indentation", units="um")
        self.indent_plot.setLabel("left", "Force", units="nN")
        self.indent_plot.setTitle("Indentation Curve")

        self.elastic_plot = pg.PlotWidget()
        self.elastic_plot.showGrid(True, True, 0.3)
        self.elastic_plot.setLabel("bottom", "Indentation", units="um")
        self.elastic_plot.setLabel("left", "Modulus", units="Pa")
        self.elastic_plot.setTitle("Elasticity Spectra")
        self.elastic_plot.setLogMode(y=True)

        self.tabs.addTab(self.force_plot, "Force")
        self.tabs.addTab(self.indent_plot, "Indentation")
        self.tabs.addTab(self.elastic_plot, "Elasticity")

        self._curve: Optional[Curve] = None

    def set_curve(self, curve: Optional[Curve]) -> None:
        self._curve = curve
        self.refresh()

    def refresh(self) -> None:
        if self._curve is None:
            self._plot_no_data()
            return

        self._plot_force_curve()
        self._plot_indentation()
        self._plot_elasticity()

    def export_current_plot(self, file_path: str) -> bool:
        current_widget = self.tabs.currentWidget()
        if current_widget is None:
            return False
        pixmap = current_widget.grab()
        return pixmap.save(file_path)

    def _plot_force_curve(self) -> None:
        self.force_plot.clear()
        self.force_plot.addLegend(offset=(10, 10))

        Z_raw = self._curve.raw_data.Z
        F_raw = self._curve.raw_data.F
        Z_cur, F_cur = self._curve.get_current_data()

        Z_raw_um = Z_raw * 1e6
        F_raw_nN = F_raw * 1e9
        Z_cur_um = Z_cur * 1e6
        F_cur_nN = F_cur * 1e9

        self.force_plot.plot(
            Z_raw_um,
            F_raw_nN,
            pen=pg.mkPen((120, 120, 120), width=1),
            name="Raw",
        )

        if not np.array_equal(Z_raw, Z_cur) or not np.array_equal(F_raw, F_cur):
            self.force_plot.plot(
                Z_cur_um,
                F_cur_nN,
                pen=pg.mkPen((0, 92, 185), width=2),
                name="Filtered",
            )

        contact_point = self._curve.get_contact_point()
        if contact_point is not None:
            z_cp, f_cp = contact_point
            self.force_plot.plot(
                [z_cp * 1e6],
                [f_cp * 1e9],
                pen=None,
                symbol="o",
                symbolSize=8,
                symbolBrush=(200, 60, 60),
                name="Contact",
            )

        self.force_plot.setLabel("bottom", "Displacement", units="um")
        self.force_plot.setLabel("left", "Force", units="nN")
        self.force_plot.setTitle("Force vs Displacement")

    def _plot_indentation(self) -> None:
        self.indent_plot.clear()

        indentation, force = self._curve.get_indentation_data()
        if indentation is None or force is None:
            self._plot_empty(self.indent_plot, "No indentation data")
            return

        self.indent_plot.plot(
            indentation * 1e6,
            force * 1e9,
            pen=pg.mkPen((20, 130, 90), width=2),
        )

    def _plot_elasticity(self) -> None:
        self.elastic_plot.clear()

        depth, modulus = self._curve.get_elasticity_spectra()
        if depth is None or modulus is None:
            self._plot_empty(self.elastic_plot, "No elasticity spectra")
            return

        self.elastic_plot.plot(
            depth * 1e6,
            modulus,
            pen=pg.mkPen((160, 90, 200), width=2),
        )

    def _plot_no_data(self) -> None:
        self._plot_empty(self.force_plot, "No curve loaded")
        self._plot_empty(self.indent_plot, "No curve loaded")
        self._plot_empty(self.elastic_plot, "No curve loaded")

    def _plot_empty(self, plot: pg.PlotWidget, message: str) -> None:
        plot.clear()
        plot.setXRange(0, 1)
        plot.setYRange(0, 1)
        text = pg.TextItem(message, color=(150, 150, 150))
        plot.addItem(text)
        text.setPos(0.5, 0.5)
