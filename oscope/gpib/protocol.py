from __future__ import annotations

import numpy as np

from oscope.models.waveform import PreambleData, WaveformData


def parse_preamble(raw: str) -> PreambleData:
    """Parse the 10 comma-separated fields from :WAVeform:PREamble? response."""
    parts = raw.strip().split(",")
    if len(parts) != 10:
        raise ValueError(f"Expected 10 preamble fields, got {len(parts)}: {raw!r}")
    return PreambleData(
        format_type=int(float(parts[0])),
        acq_type=int(float(parts[1])),
        points=int(float(parts[2])),
        count=int(float(parts[3])),
        x_increment=float(parts[4]),
        x_origin=float(parts[5]),
        x_reference=float(parts[6]),
        y_increment=float(parts[7]),
        y_origin=float(parts[8]),
        y_reference=float(parts[9]),
    )


def parse_binary_block(raw: bytes) -> np.ndarray:
    """Parse IEEE 488.2 definite-length binary block into a uint8 numpy array.

    Format: #<n><length><data>
    where <n> is a single digit giving the number of digits in <length>,
    and <length> is the byte count of <data>.
    """
    # Find the '#' header
    hash_idx = raw.find(b"#")
    if hash_idx < 0:
        raise ValueError("No IEEE 488.2 block header '#' found in response")

    n_digits = int(chr(raw[hash_idx + 1]))
    if n_digits == 0:
        raise ValueError("Indefinite-length blocks not supported")

    length_str = raw[hash_idx + 2 : hash_idx + 2 + n_digits]
    byte_count = int(length_str)
    data_start = hash_idx + 2 + n_digits
    data = raw[data_start : data_start + byte_count]

    if len(data) != byte_count:
        raise ValueError(
            f"Expected {byte_count} bytes of data, got {len(data)}"
        )

    return np.frombuffer(data, dtype=np.uint8)


def reconstruct_waveform(
    raw_data: np.ndarray, preamble: PreambleData, channel: int
) -> WaveformData:
    """Convert raw ADC values to voltage and time arrays using preamble scaling."""
    voltage = (raw_data.astype(np.float64) - preamble.y_reference) * preamble.y_increment + preamble.y_origin
    time = np.arange(len(raw_data)) * preamble.x_increment + preamble.x_origin

    return WaveformData(
        time=time,
        voltage=voltage,
        channel=channel,
        preamble=preamble,
        raw_data=raw_data,
    )
