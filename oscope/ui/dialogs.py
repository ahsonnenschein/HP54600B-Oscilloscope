from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget


def get_save_path(parent: QWidget) -> str | None:
    """Show a save file dialog and return the chosen path, or None if cancelled."""
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Waveform Data",
        "",
        "CSV Files (*.csv);;All Files (*)",
    )
    return path if path else None


def get_save_image_path(parent: QWidget) -> str | None:
    """Show a save image dialog and return the chosen path, or None if cancelled."""
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Screenshot",
        "",
        "JPEG Image (*.jpg);;PNG Image (*.png);;All Files (*)",
    )
    return path if path else None
