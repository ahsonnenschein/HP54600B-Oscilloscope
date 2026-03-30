from __future__ import annotations

import queue
from typing import Any, Callable

from PyQt6.QtCore import QThread, pyqtSignal

from oscope.gpib.commands import ScopeCommands
from oscope.gpib.connection import GpibConnection
from oscope.gpib.protocol import parse_binary_block, parse_preamble, reconstruct_waveform
from oscope.models.waveform import WaveformData


class GpibWorker(QThread):
    """Worker thread that handles all GPIB communication.

    Uses a command queue so the UI can enqueue operations without blocking.
    """

    connected = pyqtSignal(str)           # IDN string
    disconnected = pyqtSignal()
    connection_error = pyqtSignal(str)
    waveform_ready = pyqtSignal(object)   # WaveformData
    status_message = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._command_queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...]] | None] = queue.Queue()
        self._running = True
        self._continuous = False
        self._continuous_channel: int | list[int] = 1
        self._connection = GpibConnection()
        self._commands: ScopeCommands | None = None

    def run(self) -> None:
        while self._running:
            # Process any queued commands first
            try:
                item = self._command_queue.get(timeout=0.05)
            except queue.Empty:
                # No queued command — if continuous mode, do another acquisition
                if self._continuous and self._commands is not None:
                    try:
                        ch = self._continuous_channel
                        if isinstance(ch, list):
                            self._do_acquire_multi(ch)
                        else:
                            self._do_acquire(ch)
                    except Exception as e:
                        self.error.emit(str(e))
                        self._continuous = False
                        self.busy_changed.emit(False)
                        self.status_message.emit("Continuous acquisition stopped (error)")
                continue

            if item is None:
                break

            func, args = item
            self.busy_changed.emit(True)
            try:
                func(*args)
            except Exception as e:
                self.error.emit(str(e))
            finally:
                if not self._continuous:
                    self.busy_changed.emit(False)

    def enqueue(self, method: Callable[..., Any], *args: Any) -> None:
        self._command_queue.put((method, args))

    def stop(self) -> None:
        self._running = False
        self._command_queue.put(None)

    # --- High-level commands enqueued from UI ---

    def request_connect(self) -> None:
        self.enqueue(self._do_connect)

    def request_disconnect(self) -> None:
        self.enqueue(self._do_disconnect)

    def request_acquire(self, channel: int | list[int]) -> None:
        if isinstance(channel, list):
            self.enqueue(self._do_acquire_multi, channel)
        else:
            self.enqueue(self._do_acquire, channel)

    def request_set_timebase(self, range_seconds: float) -> None:
        self.enqueue(self._do_set_timebase, range_seconds)

    def request_set_channel_range(self, channel: int, range_volts: float) -> None:
        self.enqueue(self._do_set_channel_range, channel, range_volts)

    def request_set_channel_coupling(self, channel: int, coupling: str) -> None:
        self.enqueue(self._do_set_channel_coupling, channel, coupling)

    def request_set_channel_probe(self, channel: int, ratio: float) -> None:
        self.enqueue(self._do_set_channel_probe, channel, ratio)

    def request_set_trigger_sweep(self, sweep: str) -> None:
        self.enqueue(self._do_cmd, "set_trigger_sweep", sweep)

    def request_set_trigger_source(self, source: str) -> None:
        self.enqueue(self._do_cmd, "set_trigger_source", source)

    def request_set_trigger_level(self, volts: float) -> None:
        self.enqueue(self._do_cmd, "set_trigger_level", volts)

    def request_set_trigger_slope(self, slope: str) -> None:
        self.enqueue(self._do_cmd, "set_trigger_slope", slope)

    def request_set_trigger_coupling(self, coupling: str) -> None:
        self.enqueue(self._do_cmd, "set_trigger_coupling", coupling)

    def request_set_trigger_nreject(self, on: bool) -> None:
        self.enqueue(self._do_cmd, "set_trigger_noise_reject", on)

    def request_set_trigger_tv_mode(self, mode: str) -> None:
        self.enqueue(self._do_cmd, "set_trigger_tv_mode", mode)

    def request_run(self, channel: int | list[int]) -> None:
        self.enqueue(self._do_run_continuous, channel)

    def request_stop(self) -> None:
        self._continuous = False
        self.enqueue(self._do_stop)

    def request_autoscale(self) -> None:
        self.enqueue(self._do_autoscale)

    # --- Private implementations (run on worker thread) ---

    def _do_connect(self) -> None:
        self.status_message.emit("Searching for HP 54600B...")
        try:
            idn = self._connection.detect_and_connect()
            self._commands = ScopeCommands(self._connection.instrument)
            self.connected.emit(idn)
            self.status_message.emit(f"Connected: {idn}")
        except Exception as e:
            self.connection_error.emit(str(e))
            self.status_message.emit("Connection failed")
            raise

    def _do_disconnect(self) -> None:
        self._connection.disconnect()
        self._commands = None
        self.disconnected.emit()
        self.status_message.emit("Disconnected")

    def _acquire_channel(self, channel: int) -> None:
        """Acquire a single channel's waveform and emit it."""
        assert self._commands is not None

        self._commands.set_waveform_source(channel)
        self._commands.set_waveform_format_byte()
        self._commands.set_waveform_points(2000)
        self._commands.set_timebase_mode_normal()
        self._commands.digitize(channel)

        preamble_raw = self._commands.get_waveform_preamble()
        data_raw = self._commands.get_waveform_data()

        preamble = parse_preamble(preamble_raw)
        raw_array = parse_binary_block(data_raw)
        waveform = reconstruct_waveform(raw_array, preamble, channel)
        self.waveform_ready.emit(waveform)

    def _do_acquire(self, channel: int) -> None:
        assert self._commands is not None
        self.status_message.emit(f"Acquiring CH{channel}...")
        self._acquire_channel(channel)
        self.status_message.emit("Acquisition complete")

    def _do_acquire_multi(self, channels: list[int]) -> None:
        assert self._commands is not None
        self.status_message.emit(f"Acquiring CH{'+CH'.join(str(c) for c in channels)}...")
        for ch in channels:
            self._acquire_channel(ch)
        self.status_message.emit("Acquisition complete")

    def _do_set_timebase(self, range_seconds: float) -> None:
        assert self._commands is not None
        self._commands.set_timebase_range(range_seconds)
        self.status_message.emit(f"Timebase: {range_seconds:.2E} s")

    def _do_set_channel_range(self, channel: int, range_volts: float) -> None:
        assert self._commands is not None
        self._commands.set_channel_range(channel, range_volts)
        self.status_message.emit(f"CH{channel} range: {range_volts:.2E} V")

    def _do_set_channel_coupling(self, channel: int, coupling: str) -> None:
        assert self._commands is not None
        self._commands.set_channel_coupling(channel, coupling)

    def _do_set_channel_probe(self, channel: int, ratio: float) -> None:
        assert self._commands is not None
        self._commands.set_channel_probe(channel, ratio)

    def _do_cmd(self, method_name: str, *args: object) -> None:
        """Call a ScopeCommands method by name with given args."""
        assert self._commands is not None
        getattr(self._commands, method_name)(*args)

    def _do_run_continuous(self, channel: int | list[int]) -> None:
        assert self._commands is not None
        self._continuous_channel = channel
        self._continuous = True
        self.busy_changed.emit(True)
        if isinstance(channel, list):
            label = "+".join(f"CH{c}" for c in channel)
        else:
            label = f"CH{channel}"
        self.status_message.emit(f"Running continuous {label}...")

    def _do_stop(self) -> None:
        assert self._commands is not None
        self._continuous = False
        self._commands.stop()
        self.busy_changed.emit(False)
        self.status_message.emit("Stopped")

    def _do_autoscale(self) -> None:
        assert self._commands is not None
        self._commands.autoscale()
        self.status_message.emit("Autoscale complete")
