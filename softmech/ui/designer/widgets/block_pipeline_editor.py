"""Block-based pipeline editor with vertical list of colored step blocks."""

import math
from typing import Optional, Dict, List, Any, get_type_hints
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QDialog, QMessageBox, QFrame, QSpinBox, QDoubleSpinBox, QScrollArea, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QCursor

from softmech.core.pipeline import PipelineDescriptor, PipelineStep, PipelineMetadata, ProcessingStepType
from softmech.core.plugins import PluginRegistry

logger = logging.getLogger(__name__)


# Color scheme for different step types
STEP_TYPE_COLORS = {
    "filter": "#4CAF50",  # Green
    "contact_point": "#2196F3",  # Blue
    "indentation": "#FF9800",  # Orange
    "force_model": "#9C27B0",  # Purple
    "elastic_model": "#F44336",  # Red
    "elasticity_spectra": "#FF5722",  # Deep Orange
    "exporter": "#607D8B",  # Blue Grey
}


class ParametersDialog(QDialog):
    """Dialog for editing step parameters."""

    def __init__(
        self,
        step: PipelineStep,
        plugin: Optional[Any] = None,
        plugin_display_name: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.step = step
        self.param_inputs: Dict[str, QWidget] = {}
        self._plugin_class = plugin.__class__ if plugin is not None else None
        self._param_hints: Dict[str, Any] = get_type_hints(self._plugin_class) if self._plugin_class else {}
        display_name = plugin_display_name or step.plugin_id

        self.setWindowTitle(f"Edit Parameters: {display_name}")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel(f"Parameters for {display_name}")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)

        # Parameter inputs
        if not step.parameters:
            layout.addWidget(QLabel("No parameters available"))
        else:
            # Separate fitting region parameters from others
            fitting_region_params = {}
            other_params = {}
            
            for param_name, param_value in step.parameters.items():
                if param_name.startswith("min_indentation_depth") or param_name.startswith("max_indentation_depth"):
                    fitting_region_params[param_name] = param_value
                else:
                    other_params[param_name] = param_value
            
            # Add other parameters first
            for param_name, param_value in other_params.items():
                self._add_parameter_widget(layout, param_name, param_value)
            
            # Add fitting region section if present
            if fitting_region_params:
                # Separator
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                layout.addWidget(separator)
                
                # Section title
                region_title = QLabel("Fitting Region (Indentation Depth)")
                region_title.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                region_title.setStyleSheet("color: #9C27B0; margin-top: 5px;")
                layout.addWidget(region_title)
                
                # Region parameters in a grouped layout
                region_layout = QVBoxLayout()
                region_layout.setContentsMargins(20, 5, 5, 5)
                
                for param_name in sorted(fitting_region_params.keys()):
                    param_value = fitting_region_params[param_name]
                    # Create nice display names
                    if param_name == "min_indentation_depth":
                        param_display_name = "Minimum Indentation Depth"
                    elif param_name == "max_indentation_depth":
                        param_display_name = "Maximum Indentation Depth"
                    else:
                        param_display_name = param_name.replace("_", " ").title()
                    
                    param_row = QHBoxLayout()
                    param_row.addWidget(QLabel(f"{param_display_name}:"))
                    
                    # Create appropriate input widget (values in nanometers, 0-10000 nm typical)
                    input_widget = QDoubleSpinBox()
                    # Keep a large finite upper bound in the UI; treat that sentinel as +inf for max depth.
                    input_widget.setRange(0, 1e9)
                    input_widget.setDecimals(1)
                    input_widget.setSuffix(" nm")

                    numeric_value = float(param_value)
                    if param_name == "max_indentation_depth" and not math.isfinite(numeric_value):
                        input_widget.setValue(input_widget.maximum())
                        input_widget.setToolTip("Maximum indentation depth in nanometers. Set to the top value to use full available range (infinity).")
                    else:
                        input_widget.setValue(numeric_value)
                        input_widget.setToolTip("Indentation depth in nanometers. Use 0 for minimum auto-bound; use the top value for full upper range.")
                    
                    self.param_inputs[param_name] = input_widget
                    param_row.addWidget(input_widget)
                    region_layout.addLayout(param_row)
                
                layout.addLayout(region_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def _add_parameter_widget(self, layout: QVBoxLayout, param_name: str, param_value: Any) -> None:
        """Add a single parameter widget to the layout."""
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel(f"{param_name}:"))

        hinted_type = self._param_hints.get(param_name)
        if hinted_type is None:
            hinted_type = bool if isinstance(param_value, bool) else int if isinstance(param_value, int) else float if isinstance(param_value, float) else str

        min_value = getattr(self._plugin_class, f"{param_name}_min", None) if self._plugin_class else None
        max_value = getattr(self._plugin_class, f"{param_name}_max", None) if self._plugin_class else None
        odd_only = False
        if self._plugin_class:
            odd_only = bool(
                getattr(self._plugin_class, f"_{param_name}_odd", getattr(self._plugin_class, f"{param_name}_odd", False))
            )

        # Create appropriate input widget based on type
        if hinted_type is bool:
            input_widget = QComboBox()
            input_widget.addItems(["False", "True"])
            input_widget.setCurrentText("True" if bool(param_value) else "False")
        elif hinted_type is int:
            input_widget = QSpinBox()
            spin_min = int(min_value) if isinstance(min_value, (int, float)) else -1000000
            spin_max = int(max_value) if isinstance(max_value, (int, float)) else 1000000
            input_widget.setRange(spin_min, spin_max)
            input_widget.setValue(int(param_value))
            if odd_only:
                input_widget.valueChanged.connect(lambda value, w=input_widget: self._enforce_odd_spinbox(w, value))
                self._enforce_odd_spinbox(input_widget, input_widget.value())
                input_widget.setToolTip("This parameter must be an odd integer.")
        elif hinted_type is float:
            input_widget = QDoubleSpinBox()
            float_min = float(min_value) if isinstance(min_value, (int, float)) else -1e9
            float_max = float(max_value) if isinstance(max_value, (int, float)) and math.isfinite(float(max_value)) else 1e9
            input_widget.setRange(float_min, float_max)
            input_widget.setDecimals(6)
            input_widget.setValue(float(param_value))
        else:
            # Default to label for display
            input_widget = QLabel(str(param_value))

        self.param_inputs[param_name] = input_widget
        param_layout.addWidget(input_widget)
        layout.addLayout(param_layout)

    def get_parameters(self) -> Dict[str, Any]:
        """Get the edited parameters."""
        params = {}
        for param_name, widget in self.param_inputs.items():
            if isinstance(widget, QSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()
                if param_name == "max_indentation_depth" and value >= widget.maximum():
                    params[param_name] = float("inf")
                else:
                    params[param_name] = value
            elif isinstance(widget, QComboBox):
                params[param_name] = widget.currentText() == "True"
            elif isinstance(widget, QLabel):
                params[param_name] = self.step.parameters[param_name]
            else:
                params[param_name] = self.step.parameters[param_name]
        return params

    @staticmethod
    def _enforce_odd_spinbox(spinbox: QSpinBox, value: int) -> None:
        """Force odd integer values for parameters that require odd-only input."""
        if value % 2 == 0:
            corrected = value + 1 if value < spinbox.maximum() else value - 1
            spinbox.blockSignals(True)
            spinbox.setValue(corrected)
            spinbox.blockSignals(False)


class StepBlockWidget(QFrame):
    """A visual block representing a pipeline step with colored title bar."""

    delete_requested = Signal(object)  # Sends self
    edit_requested = Signal(object)  # Sends self
    algorithm_change_requested = Signal(object)  # Sends self
    add_filter_requested = Signal()  # Signal for adding filter after this one

    def __init__(
        self,
        step: PipelineStep,
        step_index: int,
        plugin_info: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.step = step
        self.step_index = step_index
        self.plugin_info = plugin_info or {}

        # Frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("StepBlockWidget { border: 2px solid #333; border-radius: 5px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar (colored)
        title_bar = QWidget()
        title_color = STEP_TYPE_COLORS.get(step.type, "#888888")
        title_bar.setStyleSheet(f"background-color: {title_color}; border-top-left-radius: 3px; border-top-right-radius: 3px;")
        title_bar.setMinimumHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 4, 8, 4)

        # Title text
        title_label = QLabel(self._get_step_display_name())
        title_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Type badge
        type_label = QLabel(f"[{step.type}]")
        type_label.setFont(QFont("Arial", 7))
        type_label.setStyleSheet("color: rgba(255, 255, 255, 180);")
        title_layout.addWidget(type_label)

        # Show About label if description is available (for all plugin types)
        if step.plugin_id != "none":
            description = self.plugin_info.get("description", "")
            if description:
                about_label = QLabel("About")
                about_label.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                about_label.setStyleSheet("color: rgba(255, 255, 255, 210); text-decoration: underline; cursor: pointer;")
                about_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                # Store the dialog method reference to avoid lambda issues
                about_label.mousePressEvent = lambda event, step=self.step, info=self.plugin_info: self._show_about_dialog(step, info)
                title_layout.addWidget(about_label)

        layout.addWidget(title_bar)

        # Content area
        content_area = QWidget()
        # Use system palette for proper color adaptation
        palette = content_area.palette()
        bg_color = palette.color(QPalette.ColorRole.Base)
        content_area.setStyleSheet(f"background-color: {bg_color.name()}; padding: 8px;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(1)

        # Parameter summary
        if step.parameters:
            for param_name, param_value in step.parameters.items():
                if isinstance(param_value, float):
                    value_text = f"{param_value:.6g}"
                else:
                    value_text = str(param_value)

                param_label = QLabel(f"{param_name}: {value_text}")
                param_label.setFont(QFont("Arial", 8))
                param_label.setStyleSheet("color: #666;")
                param_label.setWordWrap(True)
                content_layout.addWidget(param_label)

        else:
            no_param_label = QLabel("No parameters")
            no_param_label.setFont(QFont("Arial", 8))
            no_param_label.setStyleSheet("color: #999;")
            content_layout.addWidget(no_param_label)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)

        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(60)
        edit_btn.setAutoFillBackground(False)  # Inherit system styling
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self))

        change_btn = QPushButton("Change")
        change_btn.setMaximumWidth(70)
        change_btn.setAutoFillBackground(False)  # Inherit system styling
        change_btn.clicked.connect(lambda: self.algorithm_change_requested.emit(self))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(change_btn)
        
        # Only show delete and add buttons for filters
        if step.type == "filter":
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(60)
            delete_btn.setAutoFillBackground(False)  # Inherit system styling
            delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
            button_layout.addWidget(delete_btn)
            
            add_btn = QPushButton("Add")
            add_btn.setMaximumWidth(60)
            add_btn.setAutoFillBackground(False)  # Inherit system styling
            add_btn.clicked.connect(lambda: self.add_filter_requested.emit())
            button_layout.addWidget(add_btn)
        
        button_layout.addStretch()

        content_layout.addLayout(button_layout)

        layout.addWidget(content_area)

        # Set minimum size
        self.setMinimumHeight(90)

    def _build_about_tooltip(self) -> str:
        description = self.plugin_info.get("description", "") or "No description provided."
        tooltip = description

        doi_value = self.plugin_info.get("doi", "")
        doi_url = self._doi_to_url(doi_value)
        if doi_url:
            tooltip = f"{tooltip}\n\nDOI: {doi_url}"

        return tooltip

    @staticmethod
    def _doi_to_url(doi_value: str) -> str:
        doi_text = (doi_value or "").strip()
        if not doi_text:
            return ""

        if doi_text.startswith("http://") or doi_text.startswith("https://"):
            return doi_text

        doi_text = doi_text.replace("https://doi.org/", "").replace("http://doi.org/", "")
        return f"http://doi.org/{doi_text}"

    @staticmethod
    def _format_equation_text(equation: str) -> str:
        """Render a readable Unicode equation from common LaTeX-style tokens."""
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

    def _get_step_display_name(self) -> str:
        """Return user-facing title for the step block."""
        if self.step.plugin_id == "none":
            if self.step.type == "filter":
                return "No filter applied"
            if self.step.type == "contact_point":
                return "No CP detection"
            if self.step.type in ("force_model", "elastic_model"):
                return "No model fitted"
            return "None"

        return self.plugin_info.get("name", self.step.plugin_id)

    def _show_about_dialog(self, step: PipelineStep, plugin_info: Dict[str, Any]) -> None:
        """Show an About dialog with plugin information."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"About: {plugin_info.get('name', step.plugin_id)}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        # Plugin name
        name_label = QLabel(plugin_info.get("name", step.plugin_id))
        name_font = QFont("Arial", 12, QFont.Weight.Bold)
        name_label.setFont(name_font)
        layout.addWidget(name_label)
        
        # Plugin type and ID
        type_label = QLabel(f"Type: {step.type} | ID: {step.plugin_id}")
        type_font = QFont("Arial", 8)
        type_font.setItalic(True)
        type_label.setFont(type_font)
        type_label.setStyleSheet("color: #666;")
        layout.addWidget(type_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Description
        description = plugin_info.get("description", "No description available.")
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Version
        version = plugin_info.get("version", "")
        if version:
            version_label = QLabel(f"Version: {version}")
            version_label.setFont(QFont("Arial", 8))
            version_label.setStyleSheet("color: #666;")
            layout.addWidget(version_label)
        
        # Equation
        equation = plugin_info.get("equation", "")
        if equation:
            equation_text = self._format_equation_text(equation)
            equation_label = QLabel(f"Equation: {equation_text}")
            equation_label.setFont(QFont("Arial", 8))
            equation_label.setWordWrap(True)
            layout.addWidget(equation_label)
        
        # DOI
        doi_value = plugin_info.get("doi", "")
        if doi_value:
            doi_url = self._doi_to_url(doi_value)
            doi_link = QLabel(f'<a href="{doi_url}">DOI: {doi_value}</a>')
            doi_link.setOpenExternalLinks(True)
            doi_link.setTextFormat(Qt.TextFormat.RichText)
            doi_link.setFont(QFont("Arial", 8))
            layout.addWidget(doi_link)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()


class BlockBasedPipelineEditor(QWidget):
    """Vertical block-based pipeline editor with colored step blocks."""

    pipeline_changed = Signal(PipelineDescriptor)
    add_filter_requested = Signal()  # Signal for filter addition

    def __init__(self, registry: Optional[PluginRegistry] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.registry = registry or PluginRegistry()
        self.pipeline: Optional[PipelineDescriptor] = None
        self.step_widgets: List[StepBlockWidget] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Pipeline Steps")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Scroll area for blocks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container for step blocks
        self.blocks_container = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setSpacing(8)
        self.blocks_layout.setContentsMargins(4, 4, 4, 4)
        self.blocks_layout.addStretch()

        scroll.setWidget(self.blocks_container)
        main_layout.addWidget(scroll)

    def set_pipeline(self, pipeline: Optional[PipelineDescriptor]) -> None:
        """Set and display the pipeline."""
        self.pipeline = pipeline
        # Use single-shot timer to avoid flashing during batch updates
        from PySide6.QtCore import QTimer
        if hasattr(self, '_refresh_timer'):
            self._refresh_timer.stop()
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._refresh_blocks)
        self._refresh_timer.start(50)  # 50ms debounce

    def _refresh_blocks(self) -> None:
        """Refresh the visual blocks from the current pipeline."""
        # Clear existing blocks - remove from layout immediately to prevent flashing
        for widget in self.step_widgets:
            self.blocks_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self.step_widgets.clear()

        if not self.pipeline:
            return

        steps = self.pipeline.get_all_steps()

        # Create a block for each step
        for i, step in enumerate(steps):
            self._ensure_step_parameters(step)
            plugin_info = self.registry.get_info(step.plugin_id)
            block = StepBlockWidget(step, i, plugin_info=plugin_info)
            block.delete_requested.connect(self._on_delete_step)
            block.edit_requested.connect(self._on_edit_step)
            block.algorithm_change_requested.connect(self._on_change_algorithm)
            block.add_filter_requested.connect(self._add_filter)

            self.blocks_layout.insertWidget(i, block)
            self.step_widgets.append(block)

        # Don't auto-initialize default steps - wait for user to add them or load pipeline

    def _initialize_default_steps(self) -> None:
        """Initialize pipeline with default/dummy steps for required types."""
        if not self.pipeline:
            return

        # Required step types (only one allowed each)
        required_types = [
            ("contact_point", "none"),
            ("indentation", "none"),
            ("force_model", "none"),
            ("elastic_model", "none"),
        ]

        for step_type, default_plugin in required_types:
            # Get available plugins for this type
            available_plugins = self.registry.list(step_type)
            plugin_list = list(available_plugins.keys()) if isinstance(available_plugins, dict) else list(available_plugins)
            plugin_id = plugin_list[0] if plugin_list else default_plugin

            step = PipelineStep(
                type=step_type,
                plugin_id=plugin_id,
                parameters={}
            )
            self.pipeline.add_step(step)

        self._refresh_blocks()
        self.pipeline_changed.emit(self.pipeline)

    def _add_filter(self) -> None:
        """Show menu to add a filter step."""
        available_filters = self.registry.list("filter")
        filter_list = list(available_filters.keys()) if isinstance(available_filters, dict) else list(available_filters)

        if not filter_list:
            QMessageBox.warning(self, "No Filters", "No filter plugins are available.")
            return

        # Create menu
        menu = QMenu(self)
        for filter_name in filter_list:
            display_name = available_filters.get(filter_name, filter_name) if isinstance(available_filters, dict) else filter_name
            action = QAction(display_name, self)
            # Use functools.partial to properly capture filter_name
            from functools import partial
            action.triggered.connect(partial(self._do_add_filter, filter_name))
            menu.addAction(action)

        # Show menu at cursor position
        menu.exec_(QCursor.pos())

    def _do_add_filter(self, filter_name: str, checked: bool = False) -> None:
        """Actually add a filter to the pipeline."""
        if not self.pipeline:
            return

        new_filter = PipelineStep(
            type="filter",
            plugin_id=filter_name,
            parameters={}
        )

        # Populate with filter defaults
        if filter_name != "none":
            try:
                plugin = self.registry.get(filter_name)
                new_filter.parameters = plugin.get_parameters_dict()
            except Exception as e:
                logger.warning(f"Could not get defaults for filter {filter_name}: {e}")

        # Insert filter at the beginning of the pipeline (filters should come first)
        steps = self.pipeline.get_all_steps()
        
        # Find position to insert: after existing filters
        insert_pos = 0
        for i, step in enumerate(steps):
            if step.type == "filter":
                insert_pos = i + 1
            else:
                break

        # Insert into pipeline
        if hasattr(self.pipeline, 'steps'):
            self.pipeline.steps.insert(insert_pos, new_filter)
        else:
            # If using stages, insert into first stage
            if self.pipeline.stages:
                self.pipeline.stages[0].steps.insert(insert_pos, new_filter)

        # Immediately refresh without debounce for user-initiated actions
        self._refresh_blocks()
        self.pipeline_changed.emit(self.pipeline)

    def _on_delete_step(self, block: StepBlockWidget) -> None:
        """Delete a step from the pipeline."""
        if not self.pipeline:
            return

        step = block.step

        # Don't allow deleting non-filter steps (they must exist)
        if step.type != "filter":
            reply = QMessageBox.question(
                self,
                "Cannot Delete",
                f"Cannot delete {step.type} step. You can only change the algorithm.\nWould you like to change it instead?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_change_algorithm(block)
            return

        # Get all filter steps to check if this is the first one
        all_steps = self.pipeline.get_all_steps()
        filter_steps = [s for s in all_steps if s.type == "filter"]
        is_first_filter = filter_steps and filter_steps[0] == step

        if is_first_filter:
            # For the first filter, change it to "none" instead of deleting
            reply = QMessageBox.question(
                self,
                "Reset Filter",
                f"Change first filter from '{step.plugin_id}' to 'none'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                step.plugin_id = "none"
                step.parameters = {}
                self._refresh_blocks()
                self.pipeline_changed.emit(self.pipeline)
        else:
            # For other filters, allow deletion
            reply = QMessageBox.question(
                self,
                "Delete Step",
                f"Delete filter '{step.plugin_id}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if step in all_steps:
                    all_steps.remove(step)
                    
                    # Update pipeline
                    if hasattr(self.pipeline, 'steps'):
                        self.pipeline.steps = all_steps
                    else:
                        # Rebuild stages
                        if self.pipeline.stages:
                            self.pipeline.stages[0].steps = all_steps

                    self._refresh_blocks()
                    self.pipeline_changed.emit(self.pipeline)

    def _on_edit_step(self, block: StepBlockWidget) -> None:
        """Edit parameters of a step."""
        step = block.step
        self._ensure_step_parameters(step)

        plugin_instance = None
        if step.plugin_id != "none":
            try:
                plugin_instance = self.registry.get(step.plugin_id)
            except Exception:
                plugin_instance = None

        dialog = ParametersDialog(
            step,
            plugin=plugin_instance,
            plugin_display_name=block.plugin_info.get("name"),
            parent=self,
        )
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            new_params = dialog.get_parameters()
            step.parameters = new_params
            self._refresh_blocks()
            self.pipeline_changed.emit(self.pipeline)

    def _ensure_step_parameters(self, step: PipelineStep) -> None:
        """Ensure non-placeholder steps have default plugin parameters loaded."""
        if step.plugin_id == "none":
            return

        try:
            plugin = self.registry.get(step.plugin_id)
            defaults = plugin.get_parameters_dict()
            if not step.parameters:
                step.parameters = defaults
                return

            filtered_existing = {
                key: value for key, value in step.parameters.items() if key in defaults
            }
            merged = defaults.copy()
            merged.update(filtered_existing)
            step.parameters = merged
        except Exception as e:
            logger.warning(f"Could not get defaults for {step.plugin_id}: {e}")

    def _on_change_algorithm(self, block: StepBlockWidget) -> None:
        """Change the algorithm/plugin for a step."""
        step = block.step
        step_type = step.type

        available_plugins = self.registry.list(step_type)
        plugin_list = list(available_plugins.keys()) if isinstance(available_plugins, dict) else list(available_plugins)

        if not plugin_list:
            QMessageBox.warning(self, "No Plugins", f"No plugins available for type '{step_type}'.")
            return

        # Show dialog to select new plugin
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Change {step_type} Algorithm")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"Select new algorithm for {step_type}:"))

        combo = QComboBox()
        for plugin_id in plugin_list:
            display_name = available_plugins.get(plugin_id, plugin_id) if isinstance(available_plugins, dict) else plugin_id
            combo.addItem(display_name, plugin_id)
        current_idx = combo.findData(step.plugin_id)
        if current_idx >= 0:
            combo.setCurrentIndex(current_idx)
        layout.addWidget(combo)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        if dialog.exec_() == QDialog.DialogCode.Accepted:
            new_plugin_id = combo.currentData()
            if new_plugin_id != step.plugin_id:
                step.plugin_id = new_plugin_id
                step.parameters = {}  # Reset parameters when changing algorithm
                
                # Populate with plugin defaults
                if new_plugin_id != "none":
                    try:
                        plugin = self.registry.get(new_plugin_id)
                        step.parameters = plugin.get_parameters_dict()
                    except Exception as e:
                        logger.warning(f"Could not get defaults for {new_plugin_id}: {e}")
                
                self._refresh_blocks()
                self.pipeline_changed.emit(self.pipeline)
