from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QToolBar, QWidget


class ConnectionBar(QToolBar):
    """Top toolbar with connect/disconnect buttons and connection status indicator."""

    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__("Connection")
        self.setMovable(False)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e; font-weight: bold;"
            "  padding: 6px 16px; border: none; border-radius: 4px; }"
            "QPushButton:hover { background-color: #94e2d5; }"
            "QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.connect_btn.clicked.connect(self.connect_clicked.emit)
        layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet(
            "QPushButton { background-color: #f38ba8; color: #1e1e2e; font-weight: bold;"
            "  padding: 6px 16px; border: none; border-radius: 4px; }"
            "QPushButton:hover { background-color: #f5a0b8; }"
            "QPushButton:disabled { background-color: #45475a; color: #6c7086; }"
        )
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_clicked.emit)
        layout.addWidget(self.disconnect_btn)

        # Status LED
        self.status_led = QLabel()
        self.status_led.setFixedSize(16, 16)
        self._set_led_color("#f38ba8")  # red = disconnected
        layout.addWidget(self.status_led)

        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: #cdd6f4; font-family: monospace; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.addWidget(container)

    def set_connected(self, idn: str) -> None:
        self._set_led_color("#a6e3a1")
        self.status_label.setText(idn)
        self.status_label.setStyleSheet("color: #a6e3a1; font-family: monospace; font-size: 12px;")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)

    def set_disconnected(self) -> None:
        self._set_led_color("#f38ba8")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: #f38ba8; font-family: monospace; font-size: 12px;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def set_busy(self, busy: bool) -> None:
        if busy:
            self._set_led_color("#f9e2af")  # yellow
        elif self.disconnect_btn.isEnabled():
            self._set_led_color("#a6e3a1")

    def _set_led_color(self, color: str) -> None:
        self.status_led.setStyleSheet(
            f"background-color: {color}; border-radius: 8px;"
            f" border: 2px solid {color}40;"
            f" box-shadow: 0 0 6px {color};"
        )
