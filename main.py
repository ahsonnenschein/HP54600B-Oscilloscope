#!/usr/bin/env python3
"""HP 54600B Oscilloscope Control Application."""

import sys

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from oscope.ui.mainwindow import MainWindow


def apply_dark_palette(app: QApplication) -> None:
    """Apply a Catppuccin Mocha-inspired dark palette."""
    palette = QPalette()

    base = QColor(24, 24, 37)
    surface = QColor(30, 30, 46)
    overlay = QColor(49, 50, 68)
    text = QColor(205, 214, 244)
    subtext = QColor(166, 173, 200)
    blue = QColor(137, 180, 250)

    palette.setColor(QPalette.ColorRole.Window, surface)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, surface)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, overlay)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Highlight, blue)
    palette.setColor(QPalette.ColorRole.HighlightedText, base)
    palette.setColor(QPalette.ColorRole.ToolTipBase, overlay)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.PlaceholderText, subtext)
    palette.setColor(QPalette.ColorRole.Link, blue)

    # Disabled state
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, subtext)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, subtext)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, subtext)

    app.setPalette(palette)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_dark_palette(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
