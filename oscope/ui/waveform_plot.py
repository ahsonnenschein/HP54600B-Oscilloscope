from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QColor, QFont

from oscope.models.waveform import WaveformData

# Channel colors: CH1 = yellow, CH2 = cyan (classic scope colors)
CHANNEL_COLORS = {
    1: "#FFD700",
    2: "#00E5FF",
}


class WaveformPlotWidget(pg.PlotWidget):
    """Oscilloscope-style waveform display using pyqtgraph."""

    def __init__(self) -> None:
        super().__init__()

        self.setBackground(QColor(20, 20, 35))

        self.showGrid(x=True, y=True, alpha=0.25)
        self.setLabel("bottom", "Time", units="s")
        self.setLabel("left", "Voltage", units="V")

        title_font = QFont("Monospace", 11)
        self.setTitle("HP 54600B Oscilloscope", color="#aaaacc", size="11pt")

        for axis_name in ("bottom", "left"):
            axis = self.getAxis(axis_name)
            axis.setPen(pg.mkPen("#666688"))
            axis.setTextPen(pg.mkPen("#9999bb"))
            axis.setStyle(tickFont=QFont("Monospace", 9))

        self.setMouseEnabled(x=True, y=True)
        self.enableAutoRange()

        # Legend
        self._legend = self.addLegend(offset=(10, 10))
        self._legend.setLabelTextColor("#cdd6f4")

        # Trigger time marker — dashed red vertical line at t=0
        self._trigger_line = pg.InfiniteLine(
            pos=0, angle=90, movable=False,
            pen=pg.mkPen("#ff4444", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine),
            label="T", labelOpts={"color": "#ff4444", "position": 0.95},
        )
        self._trigger_line.setVisible(False)
        self.addItem(self._trigger_line, ignoreBounds=True)

        # Crosshair
        self._vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#ffffff30"))
        self._hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#ffffff30"))
        self.addItem(self._vline, ignoreBounds=True)
        self.addItem(self._hline, ignoreBounds=True)

        # Active traces per channel
        self._traces: dict[int, pg.PlotDataItem] = {}

        # Mouse tracking for crosshair
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def update_waveform(self, data: WaveformData) -> None:
        """Update or create a trace for the given channel."""
        channel = data.channel
        color = CHANNEL_COLORS.get(channel, "#00ff41")

        if channel not in self._traces:
            self._traces[channel] = self.plot(
                data.time, data.voltage,
                pen=pg.mkPen(color, width=2),
                name=f"CH{channel}",
            )
        else:
            self._traces[channel].setData(data.time, data.voltage)

        self._trigger_line.setVisible(True)
        self.enableAutoRange()
        self.autoRange()

    def clear_traces(self) -> None:
        for trace in self._traces.values():
            self.removeItem(trace)
        self._traces.clear()
        self._trigger_line.setVisible(False)

    def _on_mouse_moved(self, pos: pg.Point) -> None:
        vb = self.getViewBox()
        if vb is not None and self.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            self._vline.setPos(mouse_point.x())
            self._hline.setPos(mouse_point.y())
