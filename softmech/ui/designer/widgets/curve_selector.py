"""Shared curve selector widget used across all visualization tabs."""

from typing import Optional
import logging

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSlider, QLabel, QSpinBox, QRadioButton, QButtonGroup, QCheckBox, QPushButton
)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class CurveSelectorWidget(QWidget):
    """Shared control widget for selecting curves and view modes."""

    curve_selected = Signal(int)  # Emits curve index
    view_mode_changed = Signal(str)  # Emits "all", "average", or "selected"
    outlier_toggled = Signal()  # Emits when outlier button is clicked


    def __init__(self, show_align_cp: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.show_align_cp = show_align_cp

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Curve selection
        layout.addWidget(QLabel("Curve:"))

        self.curve_slider = QSlider(Qt.Orientation.Horizontal)
        self.curve_slider.setMinimum(0)
        self.curve_slider.setMaximum(0)
        self.curve_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.curve_slider)

        self.curve_spin = QSpinBox()
        self.curve_spin.setMinimum(0)
        self.curve_spin.setMaximum(0)
        self.curve_spin.setMinimumWidth(80)  # Make spinner wider and more usable
        self.curve_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)  # Larger buttons
        self.curve_spin.valueChanged.connect(self._on_spin_changed)
        layout.addWidget(self.curve_spin)

        # Add some spacing
        layout.addSpacing(10)

        # View mode selection
        layout.addWidget(QLabel("View:"))
        self.view_group = QButtonGroup(self)

        self.view_all_rb = QRadioButton("All")
        self.view_average_rb = QRadioButton("Average")
        self.view_selected_rb = QRadioButton("One")

        self.view_group.addButton(self.view_all_rb)
        self.view_group.addButton(self.view_average_rb)
        self.view_group.addButton(self.view_selected_rb)

        self.view_all_rb.toggled.connect(self._on_view_changed)
        self.view_average_rb.toggled.connect(self._on_view_changed)
        self.view_selected_rb.toggled.connect(self._on_view_changed)

        self.view_all_rb.setChecked(True)

        layout.addWidget(self.view_all_rb)
        layout.addWidget(self.view_average_rb)
        layout.addWidget(self.view_selected_rb)

        # CP alignment toggle (optional)
        if show_align_cp:
            from PySide6.QtWidgets import QCheckBox
            self.align_cp_cb = QCheckBox("Align to CP")
            self.align_cp_cb.setToolTip("Shift all curves to align at contact point")
            self.align_cp_cb.stateChanged.connect(self._on_align_changed)
            layout.addWidget(self.align_cp_cb)
        else:
            self.align_cp_cb = None

        # Outlier toggle button
        self.outlier_btn = QPushButton("Mark as Outlier")
        self.outlier_btn.setCheckable(True)
        self.outlier_btn.setToolTip("Toggle outlier status (outliers are excluded from analysis)")
        self.outlier_btn.setMaximumWidth(150)
        self.outlier_btn.clicked.connect(self._on_outlier_clicked)
        layout.addWidget(self.outlier_btn)

        layout.addStretch()

        self._current_index = 0

    def set_num_curves(self, n: int) -> None:
        """Set the number of curves available."""
        if n > 0:
            self.curve_slider.setMaximum(n - 1)
            self.curve_spin.setMaximum(n - 1)
            self.curve_slider.setEnabled(True)
            self.curve_spin.setEnabled(True)
        else:
            self.curve_slider.setMaximum(0)
            self.curve_spin.setMaximum(0)
            self.curve_slider.setEnabled(False)
            self.curve_spin.setEnabled(False)

    def get_current_index(self) -> int:
        """Get currently selected curve index."""
        return self._current_index

    def set_current_index(self, index: int) -> None:
        """Set current curve index and emit selection signal."""
        if self.curve_slider.maximum() < 0:
            return

        clamped = max(0, min(index, self.curve_slider.maximum()))
        self.curve_slider.blockSignals(True)
        self.curve_spin.blockSignals(True)
        self.curve_slider.setValue(clamped)
        self.curve_spin.setValue(clamped)
        self.curve_slider.blockSignals(False)
        self.curve_spin.blockSignals(False)
        self._current_index = clamped
        self.curve_selected.emit(clamped)

    def get_view_mode(self) -> str:
        """Get current view mode: 'all', 'average', or 'selected'."""
        if self.view_all_rb.isChecked():
            return "all"
        elif self.view_average_rb.isChecked():
            return "average"
        else:
            return "selected"

    def is_align_cp_enabled(self) -> bool:
        """Check if CP alignment is enabled."""
        if self.align_cp_cb:
            return self.align_cp_cb.isChecked()
        return False

    def set_align_cp_checked(self, checked: bool) -> None:
        """Set CP alignment checkbox state (if it exists)."""
        if self.align_cp_cb:
            self.align_cp_cb.setChecked(checked)

    def _on_slider_changed(self, value: int) -> None:
        self.curve_spin.blockSignals(True)
        self.curve_spin.setValue(value)
        self.curve_spin.blockSignals(False)
        self._current_index = value
        self.curve_selected.emit(value)

    def _on_spin_changed(self, value: int) -> None:
        self.curve_slider.blockSignals(True)
        self.curve_slider.setValue(value)
        self.curve_slider.blockSignals(False)
        self._current_index = value
        self.curve_selected.emit(value)

    def _on_view_changed(self, checked: bool) -> None:
        if not checked:
            return
        mode = self.get_view_mode()
        self.view_mode_changed.emit(mode)

    def _on_align_changed(self, state: int) -> None:
        # Trigger refresh by re-emitting view mode
        self.view_mode_changed.emit(self.get_view_mode())

    def _on_outlier_clicked(self) -> None:
        """Signal when outlier button is clicked."""
        self.outlier_toggled.emit()

    def set_outlier_checked(self, checked: bool) -> None:
        """Set outlier button checked state."""
        self.outlier_btn.blockSignals(True)
        self.outlier_btn.setChecked(checked)
        self.outlier_btn.blockSignals(False)
        
    def update_outlier_button_style(self, is_outlier: bool) -> None:
        """Update button text and style based on outlier status."""
        if is_outlier:
            self.outlier_btn.setText("Marked as Outlier")
            self.outlier_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        else:
            self.outlier_btn.setText("Mark as Outlier")
            self.outlier_btn.setStyleSheet("")

    def set_outlier_button_enabled(self, enabled: bool) -> None:
        """Enable/disable outlier button."""
        self.outlier_btn.setEnabled(enabled)

