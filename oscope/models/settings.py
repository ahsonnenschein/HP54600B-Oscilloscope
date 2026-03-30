from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChannelSettings:
    range_volts: float = 8.0       # full-scale across 8 divisions
    offset_volts: float = 0.0
    coupling: str = "DC"
    probe_ratio: float = 1.0


@dataclass
class TimebaseSettings:
    range_seconds: float = 1e-3   # full-scale across 10 divisions


@dataclass
class TriggerSettings:
    mode: str = "EDGE"            # EDGE or TV
    sweep: str = "AUTO"           # AUTO, NORMal, SINGle
    source: str = "CHANnel1"
    level_volts: float = 0.0
    slope: str = "POSitive"
    coupling: str = "DC"
    noise_reject: bool = False
    tv_mode: str = "FIEld1"


# V/div values available on the HP 54600B (per division)
VDIV_VALUES: list[tuple[str, float]] = [
    ("2 mV",   0.002),
    ("5 mV",   0.005),
    ("10 mV",  0.010),
    ("20 mV",  0.020),
    ("50 mV",  0.050),
    ("100 mV", 0.100),
    ("200 mV", 0.200),
    ("500 mV", 0.500),
    ("1 V",    1.0),
    ("2 V",    2.0),
    ("5 V",    5.0),
]

# Time/div values available on the HP 54600B (per division)
TDIV_VALUES: list[tuple[str, float]] = [
    ("5 ns",   5e-9),
    ("10 ns",  10e-9),
    ("20 ns",  20e-9),
    ("50 ns",  50e-9),
    ("100 ns", 100e-9),
    ("200 ns", 200e-9),
    ("500 ns", 500e-9),
    ("1 us",   1e-6),
    ("2 us",   2e-6),
    ("5 us",   5e-6),
    ("10 us",  10e-6),
    ("20 us",  20e-6),
    ("50 us",  50e-6),
    ("100 us", 100e-6),
    ("200 us", 200e-6),
    ("500 us", 500e-6),
    ("1 ms",   1e-3),
    ("2 ms",   2e-3),
    ("5 ms",   5e-3),
    ("10 ms",  10e-3),
    ("20 ms",  20e-3),
    ("50 ms",  50e-3),
    ("100 ms", 100e-3),
    ("200 ms", 200e-3),
    ("500 ms", 500e-3),
    ("1 s",    1.0),
    ("2 s",    2.0),
    ("5 s",    5.0),
]
