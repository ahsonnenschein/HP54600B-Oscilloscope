from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from oscope.export.csv_writer import save_waveform_csv
from oscope.gpib.worker import GpibWorker
from oscope.models.waveform import WaveformData
from oscope.ui.connection_bar import ConnectionBar
from oscope.ui.controls import ControlPanel
from oscope.ui.dialogs import get_save_path
from oscope.ui.waveform_plot import WaveformPlotWidget


class MainWindow(QMainWindow):
    """Main application window. Orchestrates UI components and GPIB worker."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HP 54600B Oscilloscope")
        self.setMinimumSize(1100, 700)

        self._last_waveforms: dict[int, WaveformData] = {}

        # --- Worker ---
        self._worker = GpibWorker()
        self._worker.start()

        # --- Connection toolbar ---
        self._conn_bar = ConnectionBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._conn_bar)

        # --- Central layout: plot + controls ---
        central = QWidget()
        self.setCentralWidget(central)
        h_layout = QHBoxLayout(central)
        h_layout.setContentsMargins(4, 4, 4, 4)

        self._plot = WaveformPlotWidget()
        h_layout.addWidget(self._plot, stretch=3)

        self._controls = ControlPanel()
        self._controls.setEnabled(False)  # disabled until connected
        h_layout.addWidget(self._controls, stretch=0)

        # --- Status bar ---
        self.statusBar().showMessage("Ready - click Connect to start")

        # --- Wire signals ---
        self._wire_connection_signals()
        self._wire_control_signals()
        self._wire_worker_signals()

    def _wire_connection_signals(self) -> None:
        self._conn_bar.connect_clicked.connect(self._worker.request_connect)
        self._conn_bar.disconnect_clicked.connect(self._on_disconnect_clicked)

    def _wire_control_signals(self) -> None:
        self._controls.vdiv_changed.connect(self._worker.request_set_channel_range)
        self._controls.coupling_changed.connect(self._worker.request_set_channel_coupling)
        self._controls.probe_changed.connect(self._worker.request_set_channel_probe)
        self._controls.tdiv_changed.connect(self._worker.request_set_timebase)

        # Individual trigger signals
        self._controls.trig_sweep_changed.connect(self._worker.request_set_trigger_sweep)
        self._controls.trig_source_changed.connect(self._worker.request_set_trigger_source)
        self._controls.trig_level_changed.connect(self._worker.request_set_trigger_level)
        self._controls.trig_slope_changed.connect(self._worker.request_set_trigger_slope)
        self._controls.trig_coupling_changed.connect(self._worker.request_set_trigger_coupling)
        self._controls.trig_nreject_changed.connect(self._worker.request_set_trigger_nreject)
        self._controls.trig_tv_mode_changed.connect(self._worker.request_set_trigger_tv_mode)

        self._controls.acquire_clicked.connect(self._on_acquire)
        self._controls.run_clicked.connect(self._on_run)
        self._controls.stop_clicked.connect(self._worker.request_stop)
        self._controls.autoscale_clicked.connect(self._worker.request_autoscale)
        self._controls.save_clicked.connect(self._on_save)

    def _wire_worker_signals(self) -> None:
        self._worker.connected.connect(self._on_connected)
        self._worker.disconnected.connect(self._on_disconnected)
        self._worker.connection_error.connect(self._on_connection_error)
        self._worker.waveform_ready.connect(self._on_waveform_ready)
        self._worker.status_message.connect(self.statusBar().showMessage)
        self._worker.busy_changed.connect(self._on_busy_changed)
        self._worker.error.connect(self._on_error)

    # --- Slots ---

    def _on_connected(self, idn: str) -> None:
        self._conn_bar.set_connected(idn)
        self._controls.setEnabled(True)

    def _on_disconnected(self) -> None:
        self._conn_bar.set_disconnected()
        self._controls.setEnabled(False)

    def _on_disconnect_clicked(self) -> None:
        self._worker.request_disconnect()
        self._plot.clear_traces()
        self._last_waveforms.clear()

    def _on_connection_error(self, msg: str) -> None:
        self._conn_bar.set_disconnected()
        QMessageBox.warning(self, "Connection Error", msg)

    def _on_waveform_ready(self, data: object) -> None:
        waveform = data  # type: WaveformData
        self._last_waveforms[waveform.channel] = waveform
        self._plot.update_waveform(waveform)

    def _on_busy_changed(self, busy: bool) -> None:
        self._controls.acquire_btn.setEnabled(not busy)
        self._conn_bar.set_busy(busy)

    def _on_error(self, msg: str) -> None:
        QMessageBox.warning(self, "Error", msg)

    def _on_acquire(self) -> None:
        channel = self._controls.current_channel
        self._worker.request_acquire(channel)

    def _on_run(self) -> None:
        channel = self._controls.current_channel
        self._worker.request_run(channel)

    def _on_save(self) -> None:
        if not self._last_waveforms:
            QMessageBox.information(self, "No Data", "Acquire a waveform first.")
            return

        path = get_save_path(self)
        if path:
            try:
                # Save the most recently selected channel, or both if multiple
                for ch, waveform in sorted(self._last_waveforms.items()):
                    if len(self._last_waveforms) > 1:
                        # Insert channel number before extension
                        base = path.rsplit(".", 1)
                        ch_path = f"{base[0]}_CH{ch}.{base[1]}" if len(base) > 1 else f"{path}_CH{ch}"
                    else:
                        ch_path = path
                    save_waveform_csv(ch_path, waveform)
                self.statusBar().showMessage(f"Saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", str(e))

    def closeEvent(self, event: object) -> None:
        self._worker.stop()
        self._worker.wait(5000)
        super().closeEvent(event)  # type: ignore[arg-type]
