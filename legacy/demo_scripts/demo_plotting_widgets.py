"""
Comparison demo: matplotlib vs PyQtGraph embedded in PySide6

This shows both plotting libraries side-by-side with the same AFM data
to help decide which is better for the Designer UI visualization.

Run: python demo_plotting_widgets.py
"""

import sys
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QTabWidget, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Add softmech to path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# MATPLOTLIB IMPLEMENTATION
# ============================================================================

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MatplotlibPlotWidget(QWidget):
    """Matplotlib plot embedded in PySide6."""

    def __init__(self, title="Matplotlib Plot"):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 4), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self.setWindowTitle(title)

    def plot_curve(self, Z, F, label="F-Z Curve", color='blue'):
        """Plot force vs displacement curve."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Convert to micrometers and nanoNewtons for better readability
        Z_um = Z * 1e6
        F_nN = F * 1e9
        
        ax.plot(Z_um, F_nN, color=color, linewidth=1.5, label=label)
        ax.set_xlabel('Displacement (μm)')
        ax.set_ylabel('Force (nN)')
        ax.set_title('Matplotlib: AFM Force Curve')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        self.canvas.draw()

    def plot_indentation(self, delta, E, color='red'):
        """Plot elasticity spectra."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Convert indentation to micrometers
        delta_um = delta * 1e6
        
        ax.plot(delta_um, E, color=color, linewidth=1.5)
        ax.set_xlabel('Indentation Depth (μm)')
        ax.set_ylabel('Young\'s Modulus (Pa)')
        ax.set_title('Matplotlib: Elasticity Spectra')
        ax.grid(True, alpha=0.3)
        
        # Use log scale if needed
        ax.set_yscale('log')
        
        self.canvas.draw()


# ============================================================================
# PYQTGRAPH IMPLEMENTATION
# ============================================================================

import pyqtgraph as pg


class PyQtGraphPlotWidget(QWidget):
    """PyQtGraph plot embedded in PySide6."""

    def __init__(self, title="PyQtGraph Plot"):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('bottom', 'Displacement', units='μm')
        self.plot_widget.setLabel('left', 'Force', units='nN')
        self.plot_widget.setTitle('PyQtGraph: AFM Force Curve')
        self.plot_widget.showGrid(True, True, 0.3)
        
        layout.addWidget(self.plot_widget)
        
        self.setWindowTitle(title)
        self.curve_item = None

    def plot_curve(self, Z, F, label="F-Z Curve", color='blue'):
        """Plot force vs displacement curve."""
        self.plot_widget.clear()
        
        # Convert to micrometers and nanoNewtons
        Z_um = Z * 1e6
        F_nN = F * 1e9
        
        self.curve_item = self.plot_widget.plot(
            Z_um, F_nN,
            pen=pg.mkPen(color, width=2),
            name=label
        )
        
        self.plot_widget.setLabel('bottom', 'Displacement', units='μm')
        self.plot_widget.setLabel('left', 'Force', units='nN')
        self.plot_widget.setTitle('PyQtGraph: AFM Force Curve')

    def plot_indentation(self, delta, E, color='red'):
        """Plot elasticity spectra."""
        self.plot_widget.clear()
        
        # Convert indentation to micrometers
        delta_um = delta * 1e6
        
        self.curve_item = self.plot_widget.plot(
            delta_um, E,
            pen=pg.mkPen(color, width=2)
        )
        
        self.plot_widget.setLabel('bottom', 'Indentation Depth', units='μm')
        self.plot_widget.setLabel('left', 'Young\'s Modulus', units='Pa')
        self.plot_widget.setTitle('PyQtGraph: Elasticity Spectra')
        self.plot_widget.setLogMode(y=True)


# ============================================================================
# COMPARISON WINDOW
# ============================================================================

class PlottingComparisonWindow(QMainWindow):
    """Side-by-side comparison of matplotlib vs PyQtGraph."""

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Plotting Comparison: matplotlib vs PyQtGraph")
        self.setGeometry(100, 100, 1600, 900)
        
        # Generate sample data
        self.Z, self.F, self.delta, self.E = self._generate_sample_data()
        
        # Create central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("AFM Data Visualization Comparison")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Main splitter: left (matplotlib) vs right (pyqtgraph)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Matplotlib
        left_widget = self._create_matplotlib_panel()
        splitter.addWidget(left_widget)
        
        # Right: PyQtGraph
        right_widget = self._create_pyqtgraph_panel()
        splitter.addWidget(right_widget)
        
        # Set equal sizes
        splitter.setSizes([800, 800])
        
        layout.addWidget(splitter)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        btn_force = QPushButton("Show Force Curve")
        btn_force.clicked.connect(self.show_force_curve)
        button_layout.addWidget(btn_force)
        
        btn_elasticity = QPushButton("Show Elasticity Spectra")
        btn_elasticity.clicked.connect(self.show_elasticity_spectra)
        button_layout.addWidget(btn_elasticity)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready: Click buttons to compare plots")

    def _generate_sample_data(self):
        """Generate synthetic AFM data for comparison."""
        from softmech.core.io import loaders
        from softmech.core.data import TipGeometry
        from softmech.core.data import Curve
        from softmech.core.algorithms import spectral
        
        # Try to load real synthetic data
        synth_path = Path("tools/synth.json")
        if synth_path.exists():
            try:
                data = loaders.load(str(synth_path))
                curve_dict = data["curves"][0]
                Z = np.array(curve_dict["data"]["Z"])
                F = np.array(curve_dict["data"]["F"])
                k = curve_dict["spring_constant"]
                tip_dict = curve_dict["tip"]
                
                # Create curve object
                tip = TipGeometry(
                    geometry_type=tip_dict.get("geometry", "sphere"),
                    radius=float(tip_dict.get("radius", 1e-6))
                )
                curve = Curve(Z, F, spring_constant=k, tip_geometry=tip)
                
                # Auto-detect contact point
                from scipy.signal import find_peaks
                noise_level = 1e-10 * 5
                contact_idx = np.where(F > noise_level)[0]
                if len(contact_idx) > 0:
                    z_cp = Z[contact_idx[0]]
                    f_cp = F[contact_idx[0]]
                else:
                    z_cp = np.min(Z)
                    f_cp = 0.0
                
                curve.set_contact_point(z_cp, f_cp)
                
                # Calculate indentation
                spectral.calculate_indentation(curve, zero_force=True)
                spectral.calculate_elasticity_spectra(curve, window_size=5, order=2, interpolate=True)
                
                delta, f_ind = curve.get_indentation_data()
                delta_e, e_val = curve.get_elasticity_spectra()
                
                return Z, F, delta_e, e_val
                
            except Exception as e:
                print(f"Warning: Could not load synthetic data: {e}")
        
        # Fallback: generate synthetic data
        print("Generating synthetic AFM data...")
        Z = np.linspace(-1e-6, 1e-6, 201)
        k = 0.01
        F = np.maximum((Z - 0) * k * 0.5, 0) + np.random.normal(0, 1e-11, len(Z))
        
        delta = np.linspace(0, 1e-6, 100)
        E = 5000 * (1 + 0.2 * np.sin(delta / 1e-7))  # Synthetic modulus
        
        return Z, F, delta, E

    def _create_matplotlib_panel(self):
        """Create panel with matplotlib plot."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("matplotlib")
        label.setStyleSheet("font-weight: bold; color: #0099cc; padding: 5px;")
        layout.addWidget(label)
        
        self.matplotlib_widget = MatplotlibPlotWidget()
        self.matplotlib_widget.plot_curve(self.Z, self.F)
        layout.addWidget(self.matplotlib_widget)
        
        info = QLabel(
            "✓ Static rendering (excellent for publication)\n"
            "✓ Highly customizable appearance\n"
            "✓ Built-in toolbar (zoom, pan, save)\n"
            "✗ Slower interaction for large datasets\n"
            "✗ Re-renders entire figure on update"
        )
        info.setStyleSheet("font-size: 10px; color: #666; padding: 5px; background: #f5f5f5;")
        layout.addWidget(info)
        
        return widget

    def _create_pyqtgraph_panel(self):
        """Create panel with PyQtGraph plot."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("PyQtGraph")
        label.setStyleSheet("font-weight: bold; color: #00aa00; padding: 5px;")
        layout.addWidget(label)
        
        self.pyqtgraph_widget = PyQtGraphPlotWidget()
        self.pyqtgraph_widget.plot_curve(self.Z, self.F)
        layout.addWidget(self.pyqtgraph_widget)
        
        info = QLabel(
            "✓ Very fast rendering (hardware accelerated)\n"
            "✓ Responsive interactions (zoom, pan, crosshair)\n"
            "✓ Great for real-time updates\n"
            "✗ Less customization for publication\n"
            "✗ Different aesthetic (more technical)"
        )
        info.setStyleSheet("font-size: 10px; color: #666; padding: 5px; background: #f5f5f5;")
        layout.addWidget(info)
        
        return widget

    def show_force_curve(self):
        """Show force vs displacement curves."""
        self.matplotlib_widget.plot_curve(self.Z, self.F, color='blue')
        self.pyqtgraph_widget.plot_curve(self.Z, self.F, color='blue')
        self.status_bar.showMessage("Showing: Force vs Displacement")

    def show_elasticity_spectra(self):
        """Show elasticity spectra."""
        if len(self.delta) > 0 and len(self.E) > 0:
            self.matplotlib_widget.plot_indentation(self.delta, self.E, color='red')
            self.pyqtgraph_widget.plot_indentation(self.delta, self.E, color='red')
            self.status_bar.showMessage("Showing: Elasticity Spectra E(δ)")
        else:
            self.status_bar.showMessage("No elasticity data available")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the comparison demo."""
    app = QApplication(sys.argv)
    window = PlottingComparisonWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
