from __future__ import annotations

import csv

from oscope.models.waveform import WaveformData


def save_waveform_csv(path: str, waveform: WaveformData) -> None:
    """Save waveform data to CSV with a metadata header."""
    p = waveform.preamble

    with open(path, "w", newline="") as f:
        # Metadata header
        f.write(f"# HP 54600B Waveform Data\n")
        f.write(f"# Timestamp: {waveform.timestamp}\n")
        f.write(f"# Channel: {waveform.channel}\n")
        f.write(f"# Points: {p.points}\n")
        f.write(f"# X Increment: {p.x_increment:.6E}\n")
        f.write(f"# X Origin: {p.x_origin:.6E}\n")
        f.write(f"# X Reference: {p.x_reference:.6E}\n")
        f.write(f"# Y Increment: {p.y_increment:.6E}\n")
        f.write(f"# Y Origin: {p.y_origin:.6E}\n")
        f.write(f"# Y Reference: {p.y_reference:.6E}\n")

        writer = csv.writer(f)
        writer.writerow(["Time (s)", "Voltage (V)", "Raw"])
        for i in range(len(waveform.time)):
            writer.writerow([
                f"{waveform.time[i]:.9E}",
                f"{waveform.voltage[i]:.6E}",
                int(waveform.raw_data[i]),
            ])
