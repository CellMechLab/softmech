"""Visual flowchart-based pipeline editor with cascading step boxes (Orange-style)."""

from typing import Optional, Dict
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QDialog, QGraphicsScene, QGraphicsView, QGraphicsItem, 
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QSpinBox, QDoubleSpinBox,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QFont

from softmech.core.pipeline import PipelineDescriptor, PipelineStep
from softmech.core.plugins import PluginRegistry

logger = logging.getLogger(__name__)


class PipelineStepBox(QGraphicsRectItem):
    """Visual box representing a pipeline step. Clickable to edit parameters."""

    STEP_WIDTH = 100
    STEP_HEIGHT = 60
    STEP_SPACING = 140

    def __init__(self, step: PipelineStep, index: int, x: float, y: float):
        super().__init__(x, y, self.STEP_WIDTH, self.STEP_HEIGHT)
        
        self.step = step
        self.index = index
        
        # Style the box
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setBrush(QBrush(QColor(200, 220, 255)))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Add text label (as child item, will be added automatically)
        self.label = QGraphicsTextItem(self)
        font = QFont("Courier", 8, QFont.Bold)
        self.label.setFont(font)
        label_text = f"{step.plugin_id}\n{step.type}"
        self.label.setPlainText(label_text)
        
        # Center text in box
        text_width = self.label.boundingRect().width()
        text_height = self.label.boundingRect().height()
        self.label.setX((self.STEP_WIDTH - text_width) / 2)
        self.label.setY((self.STEP_HEIGHT - text_height) / 2)

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setBrush(QBrush(QColor(100, 180, 255)))

    def hoverLeaveEvent(self, event):
        """Restore color on hover exit."""
        self.setBrush(QBrush(QColor(200, 220, 255)))


class FlowchartPipelineEditorWidget(QWidget):
    """Visual cascading pipeline editor with clickable step boxes (Orange-style)."""

    pipeline_changed = Signal(PipelineDescriptor)
    step_clicked = Signal(PipelineStep)

    def __init__(self, registry: Optional[PluginRegistry] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.registry = registry or PluginRegistry()
        self.pipeline: Optional[PipelineDescriptor] = None
        self.step_boxes: Dict[int, PipelineStepBox] = {}

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Pipeline Flowchart Editor")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)

        # Graphics scene and view for flowchart
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(150)
        self.view.setStyleSheet("border: 1px solid #ccc; background-color: #fafafa;")
        layout.addWidget(self.view)

        # Controls
        button_layout = QHBoxLayout()
        
        self.add_filter_btn = QPushButton("+ Add Filter")
        self.remove_filter_btn = QPushButton("Remove Last Filter")
        self.edit_params_btn = QPushButton("Edit Parameters")
        
        self.add_filter_btn.clicked.connect(self._show_filter_menu)
        self.remove_filter_btn.clicked.connect(self._remove_last_filter)
        self.edit_params_btn.clicked.connect(self._edit_selected_step)
        
        button_layout.addWidget(self.add_filter_btn)
        button_layout.addWidget(self.remove_filter_btn)
        button_layout.addWidget(self.edit_params_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

        # Info label
        self.info_label = QLabel("Load or create a pipeline")
        layout.addWidget(self.info_label)

    def set_pipeline(self, pipeline: Optional[PipelineDescriptor]) -> None:
        """Display a pipeline as a visual flowchart."""
        self.pipeline = pipeline
        if pipeline:
            self._refresh_diagram()

    def _refresh_diagram(self) -> None:
        """Redraw flowchart with cascading step boxes."""
        if not self.pipeline:
            self.info_label.setText("No pipeline loaded")
            return

        self.scene.clear()
        self.step_boxes.clear()

        steps = self.pipeline.get_all_steps()
        if not steps:
            self.info_label.setText("Pipeline has 0 steps")
            return

        # Draw input node
        input_box = QGraphicsRectItem(10, 50, PipelineStepBox.STEP_WIDTH, PipelineStepBox.STEP_HEIGHT)
        input_box.setPen(QPen(QColor(100, 100, 100), 2))
        input_box.setBrush(QBrush(QColor(200, 200, 200)))
        self.scene.addItem(input_box)

        input_text = QGraphicsTextItem("Input")
        input_text.setFont(QFont("Courier", 8, QFont.Bold))
        input_text.setParentItem(input_box)
        input_text.setX(20)
        input_text.setY(20)

        # Draw step boxes in cascade
        prev_x = 10 + PipelineStepBox.STEP_WIDTH
        prev_y = 50

        for i, step in enumerate(steps):
            x = prev_x + (i + 1) * PipelineStepBox.STEP_SPACING
            y = 50

            # Create step box
            step_box = PipelineStepBox(step, i, x, y)
            self.scene.addItem(step_box)
            self.step_boxes[i] = step_box

            # Draw connection from previous step
            if i == 0:
                line = QGraphicsLineItem(10 + PipelineStepBox.STEP_WIDTH, 80, x, 80)
            else:
                prev_step_box = self.step_boxes[i - 1]
                prev_right = prev_step_box.rect().right()
                line = QGraphicsLineItem(prev_right, 80, x, 80)

            line.setPen(QPen(QColor(100, 100, 100), 2))
            self.scene.addItem(line)

            # Draw arrow head
            arrow_size = 8
            end_x = x
            end_y = 80
            arrow_p1 = QPointF(end_x - arrow_size, end_y - arrow_size / 2)
            arrow_p2 = QPointF(end_x - arrow_size, end_y + arrow_size / 2)
            arrow_line1 = QGraphicsLineItem(end_x, end_y, arrow_p1.x(), arrow_p1.y())
            arrow_line2 = QGraphicsLineItem(end_x, end_y, arrow_p2.x(), arrow_p2.y())
            arrow_line1.setPen(QPen(QColor(100, 100, 100), 2))
            arrow_line2.setPen(QPen(QColor(100, 100, 100), 2))
            self.scene.addItem(arrow_line1)
            self.scene.addItem(arrow_line2)

        # Set scene rect and fit view
        self.scene.setSceneRect(0, 0, 10 + (len(steps) + 1) * PipelineStepBox.STEP_SPACING, 200)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        self.info_label.setText(f"Pipeline: {len(steps)} steps | Click a step to edit parameters")

    def _edit_selected_step(self) -> None:
        """Edit parameters of the first selected step."""
        # Get selected items from scene
        selected_items = self.scene.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Please click a step box to select it first.")
            return

        # Find the selected step box
        for item in selected_items:
            if isinstance(item, PipelineStepBox):
                self._show_parameters_dialog(item.step)
                return

    def _show_filter_menu(self) -> None:
        """Show menu to add a filter."""
        if not self.pipeline:
            QMessageBox.warning(self, "Warning", "No pipeline loaded")
            return

        filters = self.registry.list("filter")
        if not filters:
            logger.warning("No filters available")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Filter")
        layout = QVBoxLayout(dialog)

        label = QLabel("Select filter to add before Contact Point:")
        layout.addWidget(label)

        combo = QComboBox()
        for plugin_id, plugin_name in filters.items():
            combo.addItem(plugin_name, plugin_id)

        layout.addWidget(combo)

        ok_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def on_ok():
            plugin_id = combo.currentData()
            if plugin_id:
                plugin_info = self.registry.get_info(plugin_id)

                # Add filter to preprocessing stage (before contact point)
                preprocessing = self.pipeline.get_stage("preprocessing")
                if preprocessing:
                    # Find contact point step
                    cp_step_idx = None
                    for idx, s in enumerate(preprocessing.steps):
                        if s.type == "contact_point":
                            cp_step_idx = idx
                            break

                    new_step = PipelineStep(
                        type="filter",
                        plugin_id=plugin_id,
                        plugin_version=plugin_info.get("version", "1.0.0"),
                        parameters={},
                    )

                    if cp_step_idx is not None:
                        preprocessing.steps.insert(cp_step_idx, new_step)
                    else:
                        preprocessing.steps.append(new_step)

                    self.pipeline_changed.emit(self.pipeline)
                    self._refresh_diagram()

            dialog.close()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def _remove_last_filter(self) -> None:
        """Remove the last filter from the pipeline."""
        if not self.pipeline:
            return

        preprocessing = self.pipeline.get_stage("preprocessing")
        if preprocessing:
            # Find and remove last filter (before contact point)
            for i in range(len(preprocessing.steps) - 1, -1, -1):
                if preprocessing.steps[i].type == "filter":
                    preprocessing.steps.pop(i)
                    self.pipeline_changed.emit(self.pipeline)
                    self._refresh_diagram()
                    return

    def _show_parameters_dialog(self, step: PipelineStep) -> None:
        """Show dialog to edit step parameters."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Parameters: {step.plugin_id}")
        layout = QVBoxLayout(dialog)

        plugin_info = self.registry.get_info(step.plugin_id)
        plugin = self.registry.get(step.plugin_id)

        layout.addWidget(QLabel(f"Plugin: {plugin_info.get('name', step.plugin_id)}"))
        layout.addWidget(QLabel(f"Type: {step.type}"))
        layout.addWidget(QLabel(f"Version: {step.plugin_version}"))
        layout.addWidget(QLabel(""))

        # Parameter inputs
        param_widgets = {}
        layout.addWidget(QLabel("Parameters:"))

        if hasattr(plugin, "get_parameters_dict"):
            params = plugin.get_parameters_dict()
            for param_name, param_value in params.items():
                param_layout = QHBoxLayout()
                param_layout.addWidget(QLabel(f"  {param_name}:"))

                if isinstance(param_value, float):
                    widget = QDoubleSpinBox()
                    widget.setValue(param_value)
                    widget.setMinimum(-1e6)
                    widget.setMaximum(1e6)
                    widget.setSingleStep(0.01)
                elif isinstance(param_value, int):
                    widget = QSpinBox()
                    widget.setValue(param_value)
                    widget.setMinimum(-1000)
                    widget.setMaximum(10000)
                else:
                    widget = QLabel(str(param_value))

                param_layout.addWidget(widget)
                param_widgets[param_name] = widget
                layout.addLayout(param_layout)

        layout.addStretch()

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def on_ok():
            # Update step parameters
            for param_name, widget in param_widgets.items():
                if hasattr(widget, "value"):
                    step.parameters[param_name] = widget.value()

            self.pipeline_changed.emit(self.pipeline)
            dialog.close()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def get_pipeline(self) -> Optional[PipelineDescriptor]:
        """Get the current pipeline."""
        return self.pipeline

