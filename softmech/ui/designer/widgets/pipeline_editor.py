"""Simple pipeline editor for Designer."""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout

from softmech.core.pipeline import PipelineDescriptor


class PipelineEditorWidget(QWidget):
    """Minimal pipeline editor with step list and run/reset actions."""

    run_requested = Signal()
    reset_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = QLabel("Pipeline Steps")
        layout.addWidget(title)

        self.step_list = QListWidget()
        layout.addWidget(self.step_list)

        button_row = QHBoxLayout()
        self.run_button = QPushButton("Run Pipeline")
        self.reset_button = QPushButton("Reset Defaults")

        self.run_button.clicked.connect(self.run_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)

        button_row.addWidget(self.run_button)
        button_row.addWidget(self.reset_button)
        button_row.addStretch()

        layout.addLayout(button_row)
        layout.addStretch()

        self._pipeline: Optional[PipelineDescriptor] = None

    def set_pipeline(self, pipeline: Optional[PipelineDescriptor]) -> None:
        self._pipeline = pipeline
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.step_list.clear()

        if self._pipeline is None:
            self.step_list.addItem("No pipeline loaded")
            return

        steps = self._pipeline.get_all_steps()
        if not steps:
            self.step_list.addItem("Pipeline has no steps")
            return

        for step in steps:
            label = f"{step.type}: {step.plugin_id}"
            self.step_list.addItem(label)
