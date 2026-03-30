from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class PreambleData:
    format_type: int
    acq_type: int
    points: int
    count: int
    x_increment: float
    x_origin: float
    x_reference: float
    y_increment: float
    y_origin: float
    y_reference: float


@dataclass(eq=False)
class WaveformData:
    time: np.ndarray
    voltage: np.ndarray
    channel: int
    preamble: PreambleData
    raw_data: np.ndarray
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
