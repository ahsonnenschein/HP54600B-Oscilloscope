from __future__ import annotations

import time

import pyvisa


class ScopeCommands:
    """Clean Python API over HP 54600B SCPI commands.

    All methods are blocking and must be called from the worker thread only.
    """

    def __init__(self, instrument: pyvisa.resources.Resource) -> None:
        self._instr = instrument

    def _write_safe(self, cmd: str) -> None:
        """Write a command with a small settling delay."""
        self._instr.write(cmd)
        time.sleep(0.05)

    # --- System ---

    def identify(self) -> str:
        return self._instr.query("*IDN?").strip()

    def reset(self) -> None:
        self._instr.write("*RST")

    def autoscale(self) -> None:
        self._instr.write(":AUToscale")
        time.sleep(2.0)  # autoscale takes a moment

    def run(self) -> None:
        self._instr.write(":RUN")

    def stop(self) -> None:
        self._instr.write(":STOP")


    # --- Acquisition ---

    def digitize(self, channel: int) -> None:
        """Acquire waveform data. Blocks until acquisition completes."""
        self._instr.write(f":DIGitize CHANnel{channel}")
        # Wait for acquisition to complete before reading data.
        # *OPC? blocks until all pending operations finish.
        self._instr.query("*OPC?")

    def set_waveform_source(self, channel: int) -> None:
        self._instr.write(f":WAVeform:SOURce CHANnel{channel}")

    def set_waveform_format_byte(self) -> None:
        self._instr.write(":WAVeform:FORMat BYTE")

    def set_waveform_points(self, n: int = 2000) -> None:
        self._instr.write(f":WAVeform:POINts {n}")

    def get_waveform_preamble(self) -> str:
        return self._instr.query(":WAVeform:PREamble?")

    def get_waveform_data(self) -> bytes:
        self._instr.write(":WAVeform:DATA?")
        return self._instr.read_raw()

    # --- Timebase ---

    def set_timebase_range(self, seconds: float) -> None:
        self._write_safe(f":TIMebase:RANGe {seconds:.6E}")

    def set_timebase_mode_normal(self) -> None:
        self._write_safe(":TIMebase:MODE NORMal")

    # --- Channel ---

    def set_channel_range(self, channel: int, volts: float) -> None:
        self._write_safe(f":CHANnel{channel}:RANGe {volts:.6E}")

    def set_channel_offset(self, channel: int, volts: float) -> None:
        self._write_safe(f":CHANnel{channel}:OFFSet {volts:.6E}")

    def set_channel_coupling(self, channel: int, coupling: str) -> None:
        self._write_safe(f":CHANnel{channel}:COUPling {coupling}")

    def set_channel_probe(self, channel: int, ratio: float) -> None:
        self._write_safe(f":CHANnel{channel}:PROBe {ratio}")

    def set_channel_display(self, channel: int, on: bool) -> None:
        self._write_safe(f":CHANnel{channel}:DISPlay {'ON' if on else 'OFF'}")

    # --- Trigger ---

    def set_trigger_sweep(self, sweep: str) -> None:
        """Set trigger sweep: AUTO, NORMal, or SINGle."""
        self._write_safe(f":TRIGger:SWEep {sweep}")

    def set_trigger_source(self, source: str) -> None:
        self._write_safe(f":TRIGger:SOURce {source}")

    def set_trigger_level(self, volts: float) -> None:
        self._write_safe(f":TRIGger:LEVel {volts:.6E}")

    def set_trigger_slope(self, slope: str) -> None:
        self._write_safe(f":TRIGger:SLOPe {slope}")

    def set_trigger_coupling(self, coupling: str) -> None:
        self._write_safe(f":TRIGger:COUPling {coupling}")

    def set_trigger_noise_reject(self, on: bool) -> None:
        self._write_safe(f":TRIGger:NREJect {'ON' if on else 'OFF'}")

    def set_trigger_tv_mode(self, mode: str) -> None:
        self._write_safe(f":TRIGger:TV:MODE {mode}")
